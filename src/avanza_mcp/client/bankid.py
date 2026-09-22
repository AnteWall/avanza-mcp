"""Private, attempt-scoped client for Avanza's BankID protocol."""

import asyncio
import copy
import math
import time
from dataclasses import dataclass
from enum import StrEnum
from http.cookiejar import Cookie
from typing import Any
from urllib.parse import quote

import httpx

from .. import __version__

_ORIGIN = "https://www.avanza.se"
_START_PATH = "/_api/authentication/v2/sessions/bankid"
_RESTART_PATH = f"{_START_PATH}/restart"
_COLLECT_PATH = f"{_START_PATH}/collect"
_CANCEL_PATH = f"{_START_PATH}/cancel"
_SESSION_INFO_PATH = "/_api/authentication/session/info/session"
_LOGOUT_PATH = "/_api/authentication/sessions/webtoken"
_MAX_RESPONSE_BYTES = 64 * 1024


class BankIDErrorCode(StrEnum):
    CANCELLED = "cancelled"
    DENIED = "denied"
    TIMEOUT = "timeout"
    NETWORK = "network"
    MALFORMED_RESPONSE = "malformed_response"
    CUSTOMER_SELECTION = "customer_selection"
    SESSION_UNVERIFIED = "session_unverified"
    PROTOCOL = "protocol"


class BankIDError(Exception):
    """A safe error that never includes an upstream payload or credential."""

    def __init__(
        self,
        code: BankIDErrorCode,
        *,
        upstream_status: int | None = None,
    ) -> None:
        self.code = code
        self.upstream_status = upstream_status
        suffix = f"_http_{upstream_status}" if upstream_status is not None else ""
        super().__init__(f"Avanza BankID authentication failed: {code.value}{suffix}")

class CollectStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    DENIED = "denied"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, repr=False, eq=False)
class SessionMaterial:
    """Verified in-memory material; persistence is deliberately out of scope."""

    _cookies: tuple[Cookie, ...]
    _security_token: str | None

    def __repr__(self) -> str:
        return "SessionMaterial([REDACTED])"


@dataclass(frozen=True, repr=False)
class CollectResult:
    status: CollectStatus
    session: SessionMaterial | None = None

    def __post_init__(self) -> None:
        if (self.status is CollectStatus.COMPLETE) != (self.session is not None):
            raise ValueError("Only a complete result may contain session material")

    def __repr__(self) -> str:
        return f"CollectResult(status={self.status.value!r}, session=[REDACTED])"


@dataclass(frozen=True)
class _SessionInfo:
    verified: bool
    user_id: str | None = None
    security_token: str | None = None


class BankIDClient:
    """One BankID login attempt and its isolated HTTPX cookie jar."""

    def __init__(
        self,
        *,
        request_timeout: float = 20.0,
        attempt_timeout: float = 120.0,
        _transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        for name, value in (
            ("request_timeout", request_timeout),
            ("attempt_timeout", attempt_timeout),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")

        self._request_timeout = request_timeout
        self._attempt_timeout = attempt_timeout
        self._client = httpx.AsyncClient(
            base_url=_ORIGIN,
            cookies=httpx.Cookies(),
            headers={
                "Accept": "application/json",
                "User-Agent": f"avanza-mcp/{__version__}",
            },
            timeout=httpx.Timeout(request_timeout),
            follow_redirects=False,
            trust_env=False,
            transport=_transport,
        )
        self._deadline: float | None = None
        self._transaction_id: str | None = None
        self._cancelled = False
        self._closed = False
        self._inflight: set[asyncio.Task[Any]] = set()

    async def __aenter__(self) -> "BankIDClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._client.aclose()

    async def start(self) -> str:
        if self._deadline is not None:
            raise BankIDError(BankIDErrorCode.PROTOCOL)
        self._ensure_active()
        self._deadline = time.monotonic() + self._attempt_timeout
        response = await self._request(
            "POST",
            _START_PATH,
            json={"method": "QR_START", "returnScheme": "NOP"},
        )
        body = self._json_object(response)
        transaction_id = self._required_string(body, "transactionId", 512)
        qr_token = self._required_string(body, "qrToken", 4096)
        self._ensure_active()
        self._transaction_id = transaction_id
        return qr_token

    async def restart(self) -> str:
        self._ensure_started()
        response = await self._request("POST", _RESTART_PATH, json={})
        return self._required_string(self._json_object(response), "qrToken", 4096)

    async def collect(self) -> CollectResult:
        self._ensure_started()
        response = await self._request("POST", _COLLECT_PATH, json={})
        body = self._json_object(response)
        state = self._required_string(body, "state", 64)

        if state in {"OUTSTANDING_TRANSACTION", "PENDING"}:
            return CollectResult(CollectStatus.PENDING)
        if state in {"USER_CANCEL", "CANCELLED", "CANCELED"}:
            return CollectResult(CollectStatus.DENIED)
        if state == "EXPIRED_TRANSACTION":
            return CollectResult(CollectStatus.TIMED_OUT)
        if state != "COMPLETE":
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)

        session = await self._complete(body)
        self._ensure_active()
        return CollectResult(CollectStatus.COMPLETE, session)

    async def validate_session(
        self, session: SessionMaterial
    ) -> SessionMaterial | None:
        """Restore saved cookies once and return refreshed material when still valid."""
        if self._deadline is not None:
            raise BankIDError(BankIDErrorCode.PROTOCOL)
        self._ensure_active()
        self._client.cookies.clear()
        for cookie in session._cookies:
            self._client.cookies.jar.set_cookie(copy.copy(cookie))
        info = await self._get_session_info(attempt_deadline=False)
        return self._session_material(info) if info.verified else None

    async def cancel(self) -> None:
        """Invalidate locally first, then best-effort drain the obsolete attempt."""
        if self._cancelled:
            return
        self._ensure_open()
        stale = set(self._inflight)
        self._cancelled = True
        remote_error: BankIDError | None = None
        try:
            if self._transaction_id is not None:
                await self._request(
                    "POST",
                    _CANCEL_PATH,
                    json={"transactionId": self._transaction_id},
                    cleanup=True,
                    attempt_deadline=False,
                    allowed_statuses={404},
                )
        except BankIDError as error:
            remote_error = error
        finally:
            if stale:
                await asyncio.gather(*stale, return_exceptions=True)
            self._client.cookies.clear()
        if remote_error is not None:
            raise remote_error

    async def logout(self, session: SessionMaterial | None = None) -> None:
        """End the remote web session and always discard local cookies."""
        self._ensure_open()
        stale = set(self._inflight)
        self._cancelled = True
        headers: dict[str, str] = {}
        if session is not None and session._security_token is not None:
            headers["X-SecurityToken"] = session._security_token

        remote_error: BankIDError | None = None
        try:
            await self._request(
                "DELETE",
                _LOGOUT_PATH,
                headers=headers,
                cleanup=True,
                attempt_deadline=False,
                allowed_statuses={401},
            )
        except BankIDError as error:
            remote_error = error
        finally:
            if stale:
                await asyncio.gather(*stale, return_exceptions=True)
            self._client.cookies.clear()
        if remote_error is not None:
            raise remote_error

    async def _complete(self, collect_body: dict[str, Any]) -> SessionMaterial:
        info = await self._get_session_info()
        if not info.verified:
            customer_id = self._single_customer_id(collect_body)
            response = await self._request(
                "GET", f"{_COLLECT_PATH}/{quote(customer_id, safe='')}"
            )
            self._require_success(response)
            info = await self._get_session_info()
        if not info.verified:
            raise BankIDError(BankIDErrorCode.SESSION_UNVERIFIED)
        return self._session_material(info)

    async def _get_session_info(self, *, attempt_deadline: bool = True) -> _SessionInfo:
        response = await self._request(
            "GET", _SESSION_INFO_PATH, attempt_deadline=attempt_deadline
        )
        body = self._json_object(response)
        user = body.get("user")
        backend_verified = body.get("isContextVerifiedWithBackend")
        if not isinstance(user, dict) or (
            backend_verified is not None and not isinstance(backend_verified, bool)
        ):
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        logged_in = user.get("loggedIn")
        if not isinstance(logged_in, bool):
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        if not logged_in or backend_verified is False:
            return _SessionInfo(verified=False)

        user_id_value = user.get("id")
        if isinstance(user_id_value, bool) or not isinstance(user_id_value, (str, int)):
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        user_id = str(user_id_value)
        if not user_id or len(user_id) > 256:
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)

        security_token = user.get("securityToken")
        if security_token in {None, "-"}:
            security_token = None
        if security_token is not None and (
            not isinstance(security_token, str)
            or not security_token
            or len(security_token) > 4096
        ):
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        return _SessionInfo(
            verified=True,
            user_id=user_id,
            security_token=security_token,
        )

    def _session_material(self, info: _SessionInfo) -> SessionMaterial:
        if not info.verified or info.user_id is None:
            raise BankIDError(BankIDErrorCode.SESSION_UNVERIFIED)
        cookies = tuple(copy.copy(cookie) for cookie in self._client.cookies.jar)
        return SessionMaterial(
            cookies,
            info.security_token,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        cleanup: bool = False,
        attempt_deadline: bool = True,
        allowed_statuses: set[int] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self._ensure_open()
        if not cleanup:
            self._ensure_active()

        timeout = self._request_timeout
        if attempt_deadline:
            if self._deadline is None:
                raise BankIDError(BankIDErrorCode.PROTOCOL)
            timeout = min(timeout, self._deadline - time.monotonic())
            if timeout <= 0:
                raise BankIDError(BankIDErrorCode.TIMEOUT)

        task = asyncio.current_task()
        if task is not None:
            self._inflight.add(task)
        try:
            async with asyncio.timeout(timeout):
                response = await self._client.request(method, path, **kwargs)
        except TimeoutError:
            raise BankIDError(BankIDErrorCode.TIMEOUT) from None
        except httpx.TimeoutException:
            raise BankIDError(BankIDErrorCode.TIMEOUT) from None
        except httpx.TransportError:
            raise BankIDError(BankIDErrorCode.NETWORK) from None
        finally:
            if task is not None:
                self._inflight.discard(task)

        if not cleanup:
            self._ensure_active()
        if allowed_statuses is None or response.status_code not in allowed_statuses:
            self._require_success(response)
        return response

    def _require_success(self, response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        terminal = self._terminal_http_error(response)
        if terminal is not None:
            raise BankIDError(terminal)
        if response.status_code == 408:
            raise BankIDError(
                BankIDErrorCode.TIMEOUT, upstream_status=response.status_code
            )
        if response.status_code >= 500 or response.status_code == 429:
            raise BankIDError(
                BankIDErrorCode.NETWORK, upstream_status=response.status_code
            )
        raise BankIDError(
            BankIDErrorCode.PROTOCOL, upstream_status=response.status_code
        )

    def _terminal_http_error(self, response: httpx.Response) -> BankIDErrorCode | None:
        if len(response.content) > _MAX_RESPONSE_BYTES:
            return None
        try:
            body = response.json()
        except ValueError:
            return None
        if not isinstance(body, dict):
            return None
        values = {
            str(body[key]).upper()
            for key in ("state", "error", "errorCode", "code")
            if key in body
        }
        if values & {"USER_CANCEL", "CANCELLED", "CANCELED"}:
            return BankIDErrorCode.DENIED
        if "EXPIRED_TRANSACTION" in values:
            return BankIDErrorCode.TIMEOUT
        return None

    def _json_object(self, response: httpx.Response) -> dict[str, Any]:
        if len(response.content) > _MAX_RESPONSE_BYTES:
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        try:
            body = response.json()
        except ValueError:
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE) from None
        if not isinstance(body, dict):
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        return body

    @staticmethod
    def _required_string(body: dict[str, Any], field: str, maximum_length: int) -> str:
        value = body.get(field)
        if not isinstance(value, str) or not value or len(value) > maximum_length:
            raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
        return value

    @staticmethod
    def _single_customer_id(body: dict[str, Any]) -> str:
        logins = body.get("logins")
        if not isinstance(logins, list):
            raise BankIDError(BankIDErrorCode.CUSTOMER_SELECTION)
        customer_ids: list[str] = []
        for login in logins:
            if not isinstance(login, dict):
                raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
            customer_id = login.get("customerId")
            if (
                not isinstance(customer_id, str)
                or not customer_id
                or len(customer_id) > 256
            ):
                raise BankIDError(BankIDErrorCode.MALFORMED_RESPONSE)
            customer_ids.append(customer_id)
        if len(customer_ids) != 1:
            raise BankIDError(BankIDErrorCode.CUSTOMER_SELECTION)
        return customer_ids[0]

    def _ensure_open(self) -> None:
        if self._closed:
            raise BankIDError(BankIDErrorCode.PROTOCOL)

    def _ensure_active(self) -> None:
        self._ensure_open()
        if self._cancelled:
            raise BankIDError(BankIDErrorCode.CANCELLED)

    def _ensure_started(self) -> None:
        self._ensure_active()
        if self._transaction_id is None:
            raise BankIDError(BankIDErrorCode.PROTOCOL)
