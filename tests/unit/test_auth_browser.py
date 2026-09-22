"""Offline checks for the temporary local BankID browser flow."""

import json
import re
from urllib.parse import urlsplit

import httpx

from avanza_mcp.auth.browser import BrowserAuth, render_qr_svg
from avanza_mcp.auth.store import AuthStoreError
from avanza_mcp.client.bankid import (
    CollectResult,
    CollectStatus,
    SessionMaterial,
)


class FakeAttempt:
    def __init__(self):
        self.collect_results = [
            CollectResult(CollectStatus.PENDING),
            CollectResult(
                CollectStatus.COMPLETE,
                SessionMaterial((), None),
            ),
        ]
        self.cancelled = False
        self.closed = False
        self.started = 0

    async def start(self):
        self.started += 1
        return "sentinel-start-qr"

    async def restart(self):
        return "sentinel-rotated-qr"

    async def collect(self):
        return self.collect_results.pop(0)

    async def cancel(self):
        self.cancelled = True

    async def logout(self, session=None):
        self.cancelled = True

    async def validate_session(self, session):
        return session

    async def aclose(self):
        self.closed = True


class FakeStore:
    def __init__(self, session):
        self.session = session
        self.saved = 0

    async def load(self):
        return self.session

    async def save(self, session):
        self.session = session
        self.saved += 1

    async def delete(self):
        self.session = None


class FailingStore(FakeStore):
    async def load(self):
        raise AuthStoreError


async def test_browser_consent_rotates_qr_and_completes_without_secret_results():
    opened: list[str] = []
    attempt = FakeAttempt()
    auth = BrowserAuth(
        client_factory=lambda: attempt,
        qr_renderer=lambda token: f"<svg data-test='{len(token)}'></svg>",
        browser_opener=lambda url: opened.append(url) is None,
        poll_interval=0,
    )

    try:
        result = await auth.open_browser()
        assert result.state == "awaiting_approval"
        assert "sentinel" not in result.model_dump_json()
        target = urlsplit(opened[0])
        origin = f"{target.scheme}://{target.netloc}"

        async with httpx.AsyncClient(base_url=origin) as client:
            page = await client.get(target.path)
            assert page.status_code == 200
            assert "sentinel" not in page.text
            assert 'aria-label="Avanza MCP"' in page.text
            assert "You can now close this window" in page.text
            assert "not affiliated with" in page.text
            assert "Secure local connection" not in page.text
            assert "localStorage" not in page.text
            assert "sessionStorage" not in page.text
            assert page.headers["cache-control"] == "no-store"
            csrf = json.loads(re.search(r"const csrf=(\"[^\"]+\")", page.text)[1])
            headers = {"Origin": origin, "X-CSRF-Token": csrf}

            wrong_host = await client.get(target.path, headers={"Host": "evil.test"})
            assert wrong_host.status_code == 400
            rejected = await client.post(f"{target.path}/start")
            assert rejected.status_code == 403
            started = await client.post(f"{target.path}/start", headers=headers)
            assert started.json()["state"] == "scanning"

            pending = await client.get(f"{target.path}/status")
            assert pending.json()["state"] == "scanning"
            assert pending.json()["qr_svg"].startswith("<svg")
            assert "sentinel" not in pending.text

            completed = await client.get(f"{target.path}/status")
            assert completed.json()["state"] == "connected"
            assert completed.json()["qr_svg"] is None

        assert auth.status().state == "connected"
        assert auth.session is not None
        assert attempt.closed
        assert not attempt.cancelled
    finally:
        await auth.aclose()


def test_qr_renderer_returns_svg_without_embedding_payload_text():
    svg = render_qr_svg("sentinel-raw-qr-payload")
    assert svg.startswith("<svg")
    assert "sentinel-raw-qr-payload" not in svg


async def test_restored_session_reconnects_without_another_bankid_flow():
    session = SessionMaterial((), None)
    store = FakeStore(session)
    attempt = FakeAttempt()
    opened: list[str] = []
    auth = BrowserAuth(
        client_factory=lambda: attempt,
        browser_opener=lambda url: opened.append(url) is None,
        store=store,
    )

    try:
        assert (await auth.restore()).state == "connected"
        assert auth.session is not None
        assert store.saved == 1
        assert (await auth.open_browser()).state == "connected"
        assert opened == []
        assert attempt.started == 0
    finally:
        await auth.aclose()


async def test_credential_store_failure_has_safe_actionable_message():
    auth = BrowserAuth(store=FailingStore(None))

    status = await auth.restore()

    assert status.state == "error"
    assert status.error_code == "credential_store"
    assert "available and unlocked" in status.message


async def test_disconnect_requires_browser_confirmation_and_deletes_local_session():
    session = SessionMaterial((), "synthetic-token")
    store = FakeStore(session)
    attempt = FakeAttempt()
    opened: list[str] = []
    auth = BrowserAuth(
        client_factory=lambda: attempt,
        browser_opener=lambda url: opened.append(url) is None,
        store=store,
    )

    try:
        assert (await auth.restore()).state == "connected"
        assert (await auth.open_disconnect_browser()).state == "awaiting_disconnect"
        target = urlsplit(opened[0])
        origin = f"{target.scheme}://{target.netloc}"

        async with httpx.AsyncClient(base_url=origin) as client:
            page = await client.get(target.path)
            assert "Disconnect your account?" in page.text
            assert "Keep connected" in page.text
            csrf = json.loads(re.search(r"const csrf=(\"[^\"]+\")", page.text)[1])
            response = await client.post(
                f"{target.path}/disconnect",
                headers={"Origin": origin, "X-CSRF-Token": csrf},
            )
            assert response.json()["state"] == "disconnected"

        assert auth.session is None
        assert store.session is None
        assert attempt.cancelled
        assert (await auth.disconnect()).state == "disconnected"
    finally:
        await auth.aclose()
