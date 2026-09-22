"""Native credential-store persistence for verified Avanza sessions."""

import asyncio
import importlib
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.cookiejar import Cookie
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from ..client.bankid import SessionMaterial

_SERVICE = "avanza-mcp"
_ACCOUNT = "avanza-session-v1"
_MAX_RECORD_BYTES = 64 * 1024
CREDENTIAL_STORE_UNAVAILABLE = (
    "The native credential store is unavailable. Ensure macOS Keychain, Windows "
    "Credential Manager, or Linux Secret Service is available and unlocked, then retry."
)


class AuthStoreError(RuntimeError):
    """Safe credential-store failure without backend or secret details."""

    def __init__(self) -> None:
        super().__init__(CREDENTIAL_STORE_UNAVAILABLE)


class CredentialBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...

    def set_password(self, service: str, username: str, password: str) -> None: ...

    def delete_password(self, service: str, username: str) -> None: ...


class _CookieRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    name: str
    value: str | None
    port: str | None
    port_specified: bool
    domain: str
    domain_specified: bool
    domain_initial_dot: bool
    path: str
    path_specified: bool
    secure: bool
    expires: int | None
    discard: bool
    comment: str | None
    comment_url: str | None
    rest: dict[str, str | None]
    rfc2109: bool

    @classmethod
    def from_cookie(cls, cookie: Cookie) -> "_CookieRecord":
        return cls(
            version=cookie.version,
            name=cookie.name,
            value=cookie.value,
            port=cookie.port,
            port_specified=cookie.port_specified,
            domain=cookie.domain,
            domain_specified=cookie.domain_specified,
            domain_initial_dot=cookie.domain_initial_dot,
            path=cookie.path,
            path_specified=cookie.path_specified,
            secure=cookie.secure,
            expires=cookie.expires,
            discard=cookie.discard,
            comment=cookie.comment,
            comment_url=cookie.comment_url,
            rest=dict(cookie._rest),
            rfc2109=cookie.rfc2109,
        )

    def to_cookie(self) -> Cookie:
        return Cookie(**self.model_dump())


class _SessionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cookies: list[_CookieRecord]
    security_token: str | None

    @classmethod
    def from_session(cls, session: SessionMaterial) -> "_SessionRecord":
        return cls(
            cookies=[_CookieRecord.from_cookie(cookie) for cookie in session._cookies],
            security_token=session._security_token,
        )

    def to_session(self) -> SessionMaterial:
        return SessionMaterial(
            tuple(cookie.to_cookie() for cookie in self.cookies),
            self.security_token,
        )


class KeyringSessionStore:
    def __init__(self, backend: CredentialBackend, *, lock_path: Path) -> None:
        self._backend = backend
        self._lock_path = lock_path
        self._lock = asyncio.Lock()

    async def load(self) -> SessionMaterial | None:
        async with self._locked():
            payload = await self._backend_call(
                self._backend.get_password, _SERVICE, _ACCOUNT
            )
        if payload is None:
            return None
        if len(payload.encode("utf-8")) > _MAX_RECORD_BYTES:
            raise AuthStoreError
        try:
            return _SessionRecord.model_validate_json(payload).to_session()
        except (ValidationError, ValueError, TypeError):
            raise AuthStoreError from None

    async def save(self, session: SessionMaterial) -> None:
        payload = _SessionRecord.from_session(session).model_dump_json()
        if len(payload.encode("utf-8")) > _MAX_RECORD_BYTES:
            raise AuthStoreError
        async with self._locked():
            await self._backend_call(
                self._backend.set_password, _SERVICE, _ACCOUNT, payload
            )
            saved = await self._backend_call(
                self._backend.get_password, _SERVICE, _ACCOUNT
            )
        if saved != payload:
            raise AuthStoreError

    async def delete(self) -> None:
        async with self._locked():
            current = await self._backend_call(
                self._backend.get_password, _SERVICE, _ACCOUNT
            )
            if current is None:
                return
            await self._backend_call(self._backend.delete_password, _SERVICE, _ACCOUNT)
            remaining = await self._backend_call(
                self._backend.get_password, _SERVICE, _ACCOUNT
            )
        if remaining is not None:
            raise AuthStoreError

    async def _backend_call(self, function, *args):
        try:
            return await asyncio.to_thread(function, *args)
        except Exception as error:
            raise AuthStoreError from error

    @asynccontextmanager
    async def _locked(self) -> AsyncIterator[None]:
        async with self._lock:
            try:
                handle = await asyncio.to_thread(self._acquire_process_lock)
            except Exception as error:
                raise AuthStoreError from error
            try:
                yield
            finally:
                try:
                    await asyncio.to_thread(self._release_process_lock, handle)
                except Exception as error:
                    raise AuthStoreError from error

    def _acquire_process_lock(self) -> int:
        self._lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if sys.platform == "win32":
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"\0")
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX)
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    @staticmethod
    def _release_process_lock(descriptor: int) -> None:
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def create_session_store() -> KeyringSessionStore:
    backends = {
        "darwin": ("keyring.backends.macOS", "Keyring"),
        "linux": ("keyring.backends.SecretService", "Keyring"),
        "win32": ("keyring.backends.Windows", "WinVaultKeyring"),
    }
    selected = backends.get(sys.platform)
    if selected is None:
        raise AuthStoreError
    try:
        module_name, class_name = selected
        backend_class = getattr(importlib.import_module(module_name), class_name)
        if backend_class.priority <= 0:
            raise RuntimeError
        backend = backend_class()
    except Exception:
        raise AuthStoreError from None

    if sys.platform == "darwin":
        cache = Path.home() / "Library/Caches"
    elif sys.platform == "win32":
        cache = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return KeyringSessionStore(
        backend,
        lock_path=cache / "avanza-mcp/session.lock",
    )
