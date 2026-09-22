"""Offline round-trip and failure tests for native credential stores."""

from http.cookiejar import Cookie
from types import SimpleNamespace

import pytest

from avanza_mcp.auth.store import (
    AuthStoreError,
    KeyringSessionStore,
    create_session_store,
)
from avanza_mcp.client.bankid import SessionMaterial


class FakeKeyring:
    def __init__(self):
        self.value = None

    def get_password(self, service, username):
        return self.value

    def set_password(self, service, username, password):
        self.value = password

    def delete_password(self, service, username):
        self.value = None


def cookie(name, value, domain, path, *, discard, secure=False):
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=domain.startswith("."),
        path=path,
        path_specified=True,
        secure=secure,
        expires=None,
        discard=discard,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": None, "SameSite": "Lax"},
        rfc2109=False,
    )


async def test_session_round_trip_preserves_cookie_identity_and_attributes(tmp_path):
    backend = FakeKeyring()
    store = KeyringSessionStore(backend, lock_path=tmp_path / "session.lock")
    session = SessionMaterial(
        (
            cookie("session", "one", ".avanza.se", "/", discard=True),
            cookie(
                "session",
                "two",
                "www.avanza.se",
                "/_api",
                discard=False,
                secure=True,
            ),
        ),
        "synthetic-security-token",
    )

    await store.save(session)
    restored = await store.load()

    assert restored is not None
    assert restored._security_token == "synthetic-security-token"
    assert [
        (
            item.name,
            item.value,
            item.domain,
            item.path,
            item.discard,
            item.secure,
            item._rest,
        )
        for item in restored._cookies
    ] == [
        (
            item.name,
            item.value,
            item.domain,
            item.path,
            item.discard,
            item.secure,
            item._rest,
        )
        for item in session._cookies
    ]

    await store.delete()
    assert await store.load() is None
    await store.delete()


async def test_malformed_or_failed_keyring_is_safe(tmp_path):
    backend = FakeKeyring()
    store = KeyringSessionStore(backend, lock_path=tmp_path / "session.lock")
    backend.value = '{"security_token":"sentinel"}'
    with pytest.raises(AuthStoreError, match="credential store") as caught:
        await store.load()
    assert "sentinel" not in str(caught.value)

    def fail(*args):
        raise RuntimeError("sentinel-backend-secret")

    backend.get_password = fail
    with pytest.raises(AuthStoreError) as caught:
        await store.load()
    assert "sentinel" not in str(caught.value)


@pytest.mark.parametrize(
    ("platform", "module_name", "class_name"),
    [
        ("darwin", "keyring.backends.macOS", "Keyring"),
        ("linux", "keyring.backends.SecretService", "Keyring"),
        ("win32", "keyring.backends.Windows", "WinVaultKeyring"),
    ],
)
def test_platform_selects_only_native_backend(
    monkeypatch, platform, module_name, class_name
):
    class Backend(FakeKeyring):
        priority = 5

    loaded = []

    def load(name):
        loaded.append(name)
        return SimpleNamespace(**{class_name: Backend})

    monkeypatch.setattr("avanza_mcp.auth.store.sys.platform", platform)
    monkeypatch.setattr("avanza_mcp.auth.store.importlib.import_module", load)

    store = create_session_store()

    assert isinstance(store, KeyringSessionStore)
    assert loaded == [module_name]


def test_unsupported_or_unavailable_platform_fails_closed(monkeypatch):
    monkeypatch.setattr("avanza_mcp.auth.store.sys.platform", "freebsd")
    with pytest.raises(AuthStoreError, match="native credential store"):
        create_session_store()

    monkeypatch.setattr("avanza_mcp.auth.store.sys.platform", "linux")
    monkeypatch.setattr(
        "avanza_mcp.auth.store.importlib.import_module",
        lambda name: (_ for _ in ()).throw(RuntimeError("sentinel-backend-secret")),
    )
    with pytest.raises(AuthStoreError) as caught:
        create_session_store()
    assert "sentinel" not in str(caught.value)
