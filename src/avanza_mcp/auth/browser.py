"""Temporary loopback browser flow for stdio BankID authentication."""

import asyncio
import html
import io
import json
import secrets
import socket
import time
import webbrowser
from collections.abc import Callable
from contextlib import suppress
from typing import Literal, Protocol
from urllib.parse import urlsplit

import uvicorn
import qrcode
from pydantic import BaseModel
from qrcode.image.svg import SvgPathImage
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from ..client.bankid import (
    BankIDClient,
    BankIDError,
    BankIDErrorCode,
    CollectResult,
    CollectStatus,
    SessionMaterial,
)
from .page import AUTH_PAGE_TEMPLATE
from .store import AuthStoreError, CREDENTIAL_STORE_UNAVAILABLE

AuthState = Literal[
    "disconnected",
    "awaiting_approval",
    "awaiting_disconnect",
    "starting",
    "scanning",
    "connected",
    "denied",
    "timed_out",
    "error",
]

_MESSAGES: dict[AuthState, str] = {
    "disconnected": "Avanza is not connected.",
    "awaiting_approval": "Approve account access in the local browser window.",
    "awaiting_disconnect": "Confirm disconnection in the local browser window.",
    "starting": "Starting BankID authentication.",
    "scanning": "Scan the BankID QR code in the local browser window.",
    "connected": "Avanza is connected for this MCP process.",
    "denied": "BankID authentication was cancelled or denied.",
    "timed_out": "BankID authentication timed out. Start again when ready.",
    "error": "Authentication failed safely. Start again when ready.",
}


class AuthStatus(BaseModel):
    state: AuthState
    message: str
    error_code: str | None = None


class BankIDAttempt(Protocol):
    async def start(self) -> str: ...

    async def restart(self) -> str: ...

    async def collect(self) -> CollectResult: ...

    async def cancel(self) -> None: ...

    async def logout(self, session: SessionMaterial | None = None) -> None: ...

    async def validate_session(
        self, session: SessionMaterial
    ) -> SessionMaterial | None: ...

    async def aclose(self) -> None: ...


class SessionStore(Protocol):
    async def load(self) -> SessionMaterial | None: ...

    async def save(self, session: SessionMaterial) -> None: ...

    async def delete(self) -> None: ...


def render_qr_svg(payload: str) -> str:
    output = io.BytesIO()
    image = qrcode.make(payload, image_factory=SvgPathImage, box_size=8, border=4)
    image.save(output)
    svg = output.getvalue().decode("utf-8")
    return svg[svg.index("<svg") :]


class BrowserAuth:
    """Own one process-local approval, BankID attempt, and browser listener."""

    def __init__(
        self,
        *,
        client_factory: Callable[[], BankIDAttempt] = BankIDClient,
        qr_renderer: Callable[[str], str] = render_qr_svg,
        browser_opener: Callable[[str], bool] = webbrowser.open,
        store: SessionStore | None = None,
        poll_interval: float = 1.5,
        attempt_timeout: float = 120.0,
    ) -> None:
        self._client_factory = client_factory
        self._qr_renderer = qr_renderer
        self._browser_opener = browser_opener
        self._store = store
        self._poll_interval = poll_interval
        self._attempt_timeout = attempt_timeout
        self._state: AuthState = "disconnected"
        self._error_code: str | None = None
        self._qr_svg: str | None = None
        self._session: SessionMaterial | None = None
        self._attempt: BankIDAttempt | None = None
        self._last_poll = 0.0
        self._lock = asyncio.Lock()
        self._timeout_task: asyncio.Task[None] | None = None
        self._stop_task: asyncio.Task[None] | None = None
        self._server: uvicorn.Server | None = None
        self._server_task: asyncio.Task[None] | None = None
        self._origin: str | None = None
        self._path_token: str | None = None
        self._csrf_token: str | None = None

    @property
    def session(self) -> SessionMaterial | None:
        return self._session

    def status(self) -> AuthStatus:
        message = _MESSAGES[self._state]
        if self._error_code == "credential_store":
            message = CREDENTIAL_STORE_UNAVAILABLE
        elif self._error_code is not None:
            message = f"{message} Error code: {self._error_code}."
        return AuthStatus(
            state=self._state, message=message, error_code=self._error_code
        )

    async def invalidate_session(self) -> None:
        self._session = None
        self._state = "disconnected"
        self._error_code = "avanza_auth_expired"
        if self._store is not None:
            try:
                await self._store.delete()
            except AuthStoreError:
                self._state = "error"
                self._error_code = "credential_store"

    async def restore(self) -> AuthStatus:
        if self._store is None:
            return self.status()
        try:
            saved = await self._store.load()
        except AuthStoreError:
            self._state = "error"
            self._error_code = "credential_store"
            return self.status()
        if saved is None:
            return self.status()

        attempt = self._client_factory()
        try:
            validated = await attempt.validate_session(saved)
        except BankIDError as error:
            self._state = "error"
            self._error_code = self._diagnostic_code(error)
            return self.status()
        finally:
            await attempt.aclose()
        if validated is None:
            try:
                await self._store.delete()
            except AuthStoreError:
                self._state = "error"
                self._error_code = "credential_store"
                return self.status()
            self._state = "disconnected"
            return self.status()
        try:
            await self._store.save(validated)
        except AuthStoreError:
            self._state = "error"
            self._error_code = "credential_store"
            return self.status()
        self._session = validated
        self._state = "connected"
        self._error_code = None
        return self.status()

    async def open_browser(self) -> AuthStatus:
        await self._cancel_scheduled_stop()
        async with self._lock:
            if self._state == "connected":
                return self.status()
            if self._server is None:
                url = await self._start_listener()
                self._state = "awaiting_approval"
                self._error_code = None
            else:
                url = f"{self._origin}/{self._path_token}"

        opened = await asyncio.to_thread(self._browser_opener, url)
        if not opened:
            async with self._lock:
                self._state = "error"
                self._error_code = "browser_open"
            await self._stop_listener()
        return self.status()

    async def open_disconnect_browser(self) -> AuthStatus:
        await self._cancel_scheduled_stop()
        async with self._lock:
            if self._session is None:
                self._state = "disconnected"
                self._error_code = None
                return self.status()
            if self._server is None:
                url = await self._start_listener()
            else:
                url = f"{self._origin}/{self._path_token}"
            self._state = "awaiting_disconnect"
            self._error_code = None

        opened = await asyncio.to_thread(self._browser_opener, url)
        if not opened:
            async with self._lock:
                self._state = "connected"
                self._error_code = "browser_open"
            await self._stop_listener()
        return self.status()

    async def approve(self) -> AuthStatus:
        async with self._lock:
            if self._state != "awaiting_approval":
                return self.status()
            attempt = self._client_factory()
            self._attempt = attempt
            self._state = "starting"
            self._error_code = None

        try:
            qr_token = await attempt.start()
            qr_svg = self._qr_renderer(qr_token)
        except BankIDError as error:
            await attempt.aclose()
            async with self._lock:
                if self._attempt is attempt:
                    self._attempt = None
                    self._state = self._error_state(error)
                    self._error_code = self._diagnostic_code(error)
            self._schedule_listener_stop()
            return self.status()
        except RuntimeError:
            await attempt.aclose()
            async with self._lock:
                if self._attempt is attempt:
                    self._attempt = None
                    self._state = "error"
                    self._error_code = "qr_render"
            self._schedule_listener_stop()
            return self.status()

        async with self._lock:
            if self._attempt is not attempt:
                await attempt.cancel()
                await attempt.aclose()
                return self.status()
            self._qr_svg = qr_svg
            self._state = "scanning"
            self._last_poll = 0.0
            self._timeout_task = asyncio.create_task(self._expire_attempt(attempt))
        return self.status()

    async def poll(self) -> AuthStatus:
        async with self._lock:
            now = time.monotonic()
            if (
                self._state != "scanning"
                or self._attempt is None
                or now - self._last_poll < self._poll_interval
            ):
                return self.status()
            attempt = self._attempt
            self._last_poll = now

        try:
            qr_token, result = await asyncio.gather(
                attempt.restart(), attempt.collect()
            )
            qr_svg = self._qr_renderer(qr_token)
        except BankIDError as error:
            self._error_code = self._diagnostic_code(error)
            await self._finish_attempt(attempt, self._error_state(error))
            return self.status()
        except RuntimeError:
            self._error_code = "qr_render"
            await self._finish_attempt(attempt, "error")
            return self.status()

        if result.status is CollectStatus.PENDING:
            async with self._lock:
                if self._attempt is attempt:
                    self._qr_svg = qr_svg
            return self.status()
        if result.status is CollectStatus.COMPLETE and result.session is not None:
            await self._finish_attempt(attempt, "connected", result.session)
        elif result.status is CollectStatus.TIMED_OUT:
            await self._finish_attempt(attempt, "timed_out")
        else:
            await self._finish_attempt(attempt, "denied")
        return self.status()

    async def cancel(self) -> AuthStatus:
        async with self._lock:
            attempt = self._attempt
            self._attempt = None
            self._qr_svg = None
            self._state = "disconnected"
            self._error_code = None
            self._cancel_timeout()
        if attempt is not None:
            with suppress(BankIDError):
                await attempt.cancel()
            await attempt.aclose()
        self._schedule_listener_stop()
        return self.status()

    async def disconnect(self) -> AuthStatus:
        async with self._lock:
            attempt = self._attempt
            session = self._session
            self._attempt = None
            self._session = None
            self._qr_svg = None
            self._state = "disconnected"
            self._error_code = None
            self._cancel_timeout()
            if self._store is not None:
                try:
                    await self._store.delete()
                except AuthStoreError:
                    self._state = "error"
                    self._error_code = "credential_store"

        if attempt is not None:
            with suppress(BankIDError):
                await attempt.cancel()
            await attempt.aclose()
        if session is not None:
            logout = self._client_factory()
            try:
                with suppress(BankIDError):
                    await logout.logout(session)
            finally:
                await logout.aclose()
        self._schedule_listener_stop()
        return self.status()

    async def keep_connected(self) -> AuthStatus:
        async with self._lock:
            if self._session is not None:
                self._state = "connected"
                self._error_code = None
        self._schedule_listener_stop()
        return self.status()

    async def aclose(self) -> None:
        async with self._lock:
            attempt = self._attempt
            self._attempt = None
            self._qr_svg = None
            self._cancel_timeout()
        if attempt is not None:
            with suppress(BankIDError):
                await attempt.cancel()
            await attempt.aclose()
        stop_task = self._stop_task
        if stop_task is not None and stop_task is not asyncio.current_task():
            stop_task.cancel()
            with suppress(asyncio.CancelledError):
                await stop_task
        await self._stop_listener()

    async def _finish_attempt(
        self,
        attempt: BankIDAttempt,
        state: AuthState,
        session: SessionMaterial | None = None,
    ) -> None:
        logout_session = None
        async with self._lock:
            if self._attempt is not attempt:
                return
            if state == "connected" and session is not None and self._store is not None:
                try:
                    await self._store.save(session)
                except AuthStoreError:
                    logout_session = session
                    state = "error"
                    session = None
                    self._error_code = "credential_store"
            self._attempt = None
            self._qr_svg = None
            self._session = session
            self._state = state
            if state != "error":
                self._error_code = None
            self._cancel_timeout()
        if logout_session is not None:
            with suppress(BankIDError):
                await attempt.logout(logout_session)
        if state != "connected":
            with suppress(BankIDError):
                await attempt.cancel()
        await attempt.aclose()
        self._schedule_listener_stop()

    async def _expire_attempt(self, attempt: BankIDAttempt) -> None:
        try:
            await asyncio.sleep(self._attempt_timeout)
            await self._finish_attempt(attempt, "timed_out")
        except asyncio.CancelledError:
            pass

    def _cancel_timeout(self) -> None:
        if self._timeout_task is not None:
            if self._timeout_task is not asyncio.current_task():
                self._timeout_task.cancel()
            self._timeout_task = None

    @staticmethod
    def _error_state(error: BankIDError) -> AuthState:
        if error.code in {BankIDErrorCode.CANCELLED, BankIDErrorCode.DENIED}:
            return "denied"
        if error.code is BankIDErrorCode.TIMEOUT:
            return "timed_out"
        return "error"

    @staticmethod
    def _diagnostic_code(error: BankIDError) -> str:
        if error.upstream_status is not None:
            return f"{error.code.value}_http_{error.upstream_status}"
        return error.code.value

    async def _start_listener(self) -> str:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        self._origin = f"http://127.0.0.1:{port}"
        self._path_token = secrets.token_urlsafe(32)
        self._csrf_token = secrets.token_urlsafe(32)
        app = Starlette(
            routes=[
                Route(f"/{self._path_token}", self._page, methods=["GET"]),
                Route(f"/{self._path_token}/start", self._start, methods=["POST"]),
                Route(
                    f"/{self._path_token}/status", self._browser_status, methods=["GET"]
                ),
                Route(f"/{self._path_token}/cancel", self._cancel, methods=["POST"]),
                Route(
                    f"/{self._path_token}/disconnect",
                    self._disconnect,
                    methods=["POST"],
                ),
                Route(f"/{self._path_token}/keep", self._keep, methods=["POST"]),
            ]
        )
        config = uvicorn.Config(
            app,
            log_config=None,
            log_level="critical",
            access_log=False,
            lifespan="off",
            ws="none",
        )
        self._server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._server.serve(sockets=[listener]))
        for _ in range(100):
            if self._server.started:
                break
            if self._server_task.done():
                listener.close()
                raise RuntimeError("Could not start the local authentication page")
            await asyncio.sleep(0.01)
        else:
            await self._stop_listener()
            raise RuntimeError("Could not start the local authentication page")
        return f"{self._origin}/{self._path_token}"

    async def _stop_listener(self) -> None:
        server, task = self._server, self._server_task
        self._server = None
        self._server_task = None
        self._origin = None
        self._path_token = None
        self._csrf_token = None
        if server is not None:
            server.should_exit = True
        if task is not None and task is not asyncio.current_task():
            with suppress(asyncio.CancelledError):
                await task

    def _schedule_listener_stop(self) -> None:
        if self._server is not None and (
            self._stop_task is None or self._stop_task.done()
        ):
            self._stop_task = asyncio.create_task(self._stop_listener_later())

    async def _cancel_scheduled_stop(self) -> None:
        task = self._stop_task
        self._stop_task = None
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def _stop_listener_later(self) -> None:
        await asyncio.sleep(2)
        await self._stop_listener()

    def _valid_host(self, request: Request) -> bool:
        return (
            self._origin is not None
            and request.headers.get("host") == urlsplit(self._origin).netloc
        )

    def _valid_mutation(self, request: Request) -> bool:
        return (
            self._valid_host(request)
            and request.headers.get("origin") == self._origin
            and self._csrf_token is not None
            and secrets.compare_digest(
                request.headers.get("x-csrf-token", ""), self._csrf_token
            )
        )

    def _headers(self, *, nonce: str | None = None) -> dict[str, str]:
        script = f"'nonce-{nonce}'" if nonce is not None else "'none'"
        return {
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; base-uri 'none'; form-action 'none'; "
                f"script-src {script}; style-src {script}; connect-src 'self'; "
                "frame-ancestors 'none'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }

    async def _page(self, request: Request) -> Response:
        if not self._valid_host(request):
            return Response(status_code=400, headers=self._headers())
        nonce = secrets.token_urlsafe(18)
        csrf = json.dumps(self._csrf_token)
        path = json.dumps(f"/{self._path_token}")
        disconnecting = self._state == "awaiting_disconnect"
        title = "Disconnect your account?" if disconnecting else "Connect your account"
        lead = (
            "Remove the saved Avanza session from this device."
            if disconnecting
            else "Sign in with BankID to enable read-only account tools."
        )
        helper = (
            "This stops account access until you connect again."
            if disconnecting
            else "Approve access to continue with BankID."
        )
        primary = "Disconnect" if disconnecting else "Approve and continue"
        secondary = "Keep connected" if disconnecting else "Cancel"
        disconnect_mode = json.dumps(disconnecting)
        page = AUTH_PAGE_TEMPLATE.substitute(
            nonce=nonce,
            title=html.escape(title),
            lead=html.escape(lead),
            status=html.escape(_MESSAGES[self._state]),
            helper=html.escape(helper),
            primary=html.escape(primary),
            secondary=html.escape(secondary),
            csrf=csrf,
            path=path,
            disconnect_mode=disconnect_mode,
        )
        return HTMLResponse(page, headers=self._headers(nonce=nonce))

    async def _start(self, request: Request) -> Response:
        if not self._valid_mutation(request):
            return Response(status_code=403, headers=self._headers())
        status = await self.approve()
        return JSONResponse(status.model_dump(), headers=self._headers())

    async def _browser_status(self, request: Request) -> Response:
        if not self._valid_host(request):
            return Response(status_code=400, headers=self._headers())
        status = await self.poll()
        body = status.model_dump()
        body["qr_svg"] = self._qr_svg
        return JSONResponse(body, headers=self._headers())

    async def _cancel(self, request: Request) -> Response:
        if not self._valid_mutation(request):
            return Response(status_code=403, headers=self._headers())
        status = await self.cancel()
        return JSONResponse(status.model_dump(), headers=self._headers())

    async def _disconnect(self, request: Request) -> Response:
        if not self._valid_mutation(request):
            return Response(status_code=403, headers=self._headers())
        status = await self.disconnect()
        return JSONResponse(status.model_dump(), headers=self._headers())

    async def _keep(self, request: Request) -> Response:
        if not self._valid_mutation(request):
            return Response(status_code=403, headers=self._headers())
        status = await self.keep_connected()
        return JSONResponse(status.model_dump(), headers=self._headers())
