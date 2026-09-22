"""Offline protocol tests for the private BankID client."""

import asyncio
import copy
import json
import traceback

import httpx
import pytest

from avanza_mcp.client.bankid import (
    BankIDClient,
    BankIDError,
    BankIDErrorCode,
    CollectStatus,
    SessionMaterial,
)

ORIGIN = "https://www.avanza.se"
START = "/_api/authentication/v2/sessions/bankid"
RESTART = f"{START}/restart"
COLLECT = f"{START}/collect"
CANCEL = f"{START}/cancel"
INFO = "/_api/authentication/session/info/session"
LOGOUT = "/_api/authentication/sessions/webtoken"


def response(status: int = 200, body=None, **kwargs) -> httpx.Response:
    if body is not None:
        kwargs["json"] = body
    return httpx.Response(status, **kwargs)


def started() -> dict[str, str]:
    return {
        "transactionId": "synthetic-transaction",
        "autostartToken": "synthetic-autostart",
        "qrToken": "synthetic-qr",
    }


def session_info(logged_in: bool) -> dict:
    return {
        "user": {
            "loggedIn": logged_in,
            "id": "synthetic-user" if logged_in else None,
            "greetingName": "Synthetic User" if logged_in else None,
            "securityToken": "synthetic-security-token" if logged_in else "-",
        },
        "isContextVerifiedWithBackend": logged_in,
    }


async def start_client(handler, **kwargs) -> BankIDClient:
    client = BankIDClient(_transport=httpx.MockTransport(handler), **kwargs)
    await client.start()
    return client


async def test_start_restart_pending_and_transport_security():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == START:
            assert json.loads(request.content) == {
                "method": "QR_START",
                "returnScheme": "NOP",
            }
            return response(
                body=started(),
                headers={"set-cookie": "attempt=one; Path=/; HttpOnly; Secure"},
            )
        if request.url.path == RESTART:
            return response(body={"qrToken": "synthetic-qr-2"})
        assert request.url.path == COLLECT
        assert request.headers["cookie"] == "attempt=one"
        return response(body={"state": "OUTSTANDING_TRANSACTION"})

    async with await start_client(handler) as client:
        assert await client.restart() == "synthetic-qr-2"
        assert (await client.collect()).status is CollectStatus.PENDING

    assert all(request.url.scheme == "https" for request in requests)
    assert all(request.url.host == "www.avanza.se" for request in requests)
    assert len(requests) == 3


async def test_complete_selects_one_customer_and_reverifies():
    info_calls = 0
    paths: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal info_calls
        paths.append((request.method, request.url.path))
        if request.url.path == START:
            return response(
                body=started(),
                headers={"set-cookie": "session=synthetic; Path=/; HttpOnly"},
            )
        if request.url.path == COLLECT:
            return response(
                body={
                    "state": "COMPLETE",
                    "logins": [{"customerId": "synthetic-customer"}],
                }
            )
        if request.url.path == INFO:
            info_calls += 1
            return response(body=session_info(info_calls == 2))
        assert request.url.path == f"{COLLECT}/synthetic-customer"
        return response(content=b"")

    async with await start_client(handler) as client:
        result = await client.collect()

    assert result.status is CollectStatus.COMPLETE
    assert result.session is not None
    assert result.session._security_token == "synthetic-security-token"
    assert info_calls == 2
    assert paths[-3:] == [
        ("GET", INFO),
        ("GET", f"{COLLECT}/synthetic-customer"),
        ("GET", INFO),
    ]
    secret_text = f"{result!r} {result.session!r}"
    assert "synthetic-security-token" not in secret_text
    assert "synthetic" not in repr(result.session)


async def test_complete_alone_is_never_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == START:
            return response(body=started())
        if request.url.path == COLLECT and request.method == "POST":
            return response(
                body={
                    "state": "COMPLETE",
                    "logins": [{"customerId": "only-customer"}],
                }
            )
        if request.url.path == INFO:
            return response(body=session_info(False))
        return response(content=b"")

    async with await start_client(handler) as client:
        with pytest.raises(BankIDError) as caught:
            await client.collect()
    assert caught.value.code is BankIDErrorCode.SESSION_UNVERIFIED


@pytest.mark.parametrize(
    ("state", "status"),
    [
        ("PENDING", CollectStatus.PENDING),
        ("USER_CANCEL", CollectStatus.DENIED),
        ("CANCELLED", CollectStatus.DENIED),
        ("EXPIRED_TRANSACTION", CollectStatus.TIMED_OUT),
    ],
)
async def test_collect_terminal_outcomes(state, status):
    async def handler(request: httpx.Request) -> httpx.Response:
        return response(
            body=started() if request.url.path == START else {"state": state}
        )

    async with await start_client(handler) as client:
        assert (await client.collect()).status is status


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"errorCode": "USER_CANCEL"}, BankIDErrorCode.DENIED),
        ({"state": "CANCELLED"}, BankIDErrorCode.DENIED),
        ({"error": "EXPIRED_TRANSACTION"}, BankIDErrorCode.TIMEOUT),
    ],
)
async def test_non_success_terminal_responses_are_classified(body, code):
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == START:
            return response(body=started())
        return response(400, body=body)

    async with await start_client(handler) as client:
        with pytest.raises(BankIDError) as caught:
            await client.collect()
    assert caught.value.code is code


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"state": "UNKNOWN"}, BankIDErrorCode.MALFORMED_RESPONSE),
        ({"state": "COMPLETE", "logins": []}, BankIDErrorCode.CUSTOMER_SELECTION),
        (
            {
                "state": "COMPLETE",
                "logins": [{"customerId": "one"}, {"customerId": "two"}],
            },
            BankIDErrorCode.CUSTOMER_SELECTION,
        ),
    ],
)
async def test_malformed_and_customer_selection_are_distinct(body, code):
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == START:
            return response(body=started())
        if request.url.path == INFO:
            return response(body=session_info(False))
        return response(body=body)

    async with await start_client(handler) as client:
        with pytest.raises(BankIDError) as caught:
            await client.collect()
    assert caught.value.code is code


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (httpx.ConnectError("sentinel-network-secret"), BankIDErrorCode.NETWORK),
        (httpx.ReadTimeout("sentinel-timeout-secret"), BankIDErrorCode.TIMEOUT),
    ],
)
async def test_transport_failures_are_distinct_and_sanitized(failure, code):
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise failure

    async with BankIDClient(_transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(BankIDError) as caught:
            await client.start()
    assert caught.value.code is code
    assert "sentinel" not in str(caught.value)
    assert "sentinel" not in repr(caught.value)
    assert "sentinel" not in "".join(traceback.format_exception(caught.value))
    assert calls == 1


async def test_redirect_is_rejected_without_following():
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response(302, headers={"location": "https://attacker.invalid/secret"})

    async with BankIDClient(_transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(BankIDError) as caught:
            await client.start()
    assert caught.value.code is BankIDErrorCode.PROTOCOL
    assert caught.value.upstream_status == 302
    assert calls == 1


async def test_overall_attempt_deadline_bounds_later_requests(monkeypatch):
    now = 10.0
    monkeypatch.setattr("avanza_mcp.client.bankid.time.monotonic", lambda: now)

    async def handler(request: httpx.Request) -> httpx.Response:
        return response(body=started())

    async with BankIDClient(
        attempt_timeout=1, _transport=httpx.MockTransport(handler)
    ) as client:
        await client.start()
        now = 12.0
        with pytest.raises(BankIDError) as caught:
            await client.restart()
    assert caught.value.code is BankIDErrorCode.TIMEOUT


async def test_cancel_drains_stale_collect_without_leaking_into_replacement():
    collect_entered = asyncio.Event()
    release_collect = asyncio.Event()
    cancel_seen = asyncio.Event()

    async def old_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == START:
            return response(body=started())
        if request.url.path == COLLECT:
            collect_entered.set()
            await release_collect.wait()
            return response(
                body={"state": "COMPLETE"},
                headers={"set-cookie": "stale=secret; Path=/"},
            )
        assert request.url.path == CANCEL
        cancel_seen.set()
        release_collect.set()
        return response(content=b"")

    replacement_cookies: list[str | None] = []

    async def replacement_handler(request: httpx.Request) -> httpx.Response:
        replacement_cookies.append(request.headers.get("cookie"))
        return response(body=started())

    async with await start_client(old_handler) as old:
        stale_collect = asyncio.create_task(old.collect())
        await collect_entered.wait()
        await old.cancel()
        await cancel_seen.wait()
        with pytest.raises(BankIDError) as caught:
            await stale_collect
        assert caught.value.code is BankIDErrorCode.CANCELLED

        async with BankIDClient(
            _transport=httpx.MockTransport(replacement_handler)
        ) as replacement:
            await replacement.start()

    assert replacement_cookies == [None]


async def test_cancel_and_logout_are_strict_and_clear_local_cookies():
    requests: list[httpx.Request] = []
    info_calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal info_calls
        requests.append(request)
        if request.url.path == START:
            return response(
                body=started(), headers={"set-cookie": "session=secret; Path=/"}
            )
        if request.url.path == COLLECT:
            return response(body={"state": "COMPLETE"})
        if request.url.path == INFO:
            info_calls += 1
            return response(body=session_info(True))
        if request.url.path == LOGOUT:
            assert request.headers["x-securitytoken"] == "synthetic-security-token"
            return response(401)
        assert request.url.path == CANCEL
        assert json.loads(request.content) == {"transactionId": "synthetic-transaction"}
        return response(404)

    cancel_client = await start_client(handler)
    await cancel_client.cancel()
    assert list(cancel_client._client.cookies.jar) == []
    await cancel_client.aclose()

    logout_client = await start_client(handler)
    result = await logout_client.collect()
    await logout_client.logout(result.session)
    assert list(logout_client._client.cookies.jar) == []
    await logout_client.aclose()

    assert sum(request.url.path == CANCEL for request in requests) == 1
    assert sum(request.url.path == LOGOUT for request in requests) == 1


async def test_saved_session_is_restored_and_revalidated_without_start():
    seen_cookie = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_cookie
        assert request.url.path == INFO
        seen_cookie = request.headers.get("cookie")
        return response(
            body=session_info(True),
            headers={"set-cookie": "rotated=fresh; Path=/; HttpOnly; Secure"},
        )

    source = await start_client(
        lambda request: response(
            body=started(),
            headers={"set-cookie": "saved=secret; Path=/; HttpOnly; Secure"},
        )
    )
    saved = SessionMaterial(
        tuple(copy.copy(cookie) for cookie in source._client.cookies.jar),
        None,
    )
    await source.aclose()

    async with BankIDClient(_transport=httpx.MockTransport(handler)) as restored:
        material = await restored.validate_session(saved)

    assert seen_cookie == "saved=secret"
    assert material is not None
    assert {cookie.name for cookie in material._cookies} == {"saved", "rotated"}


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_deadlines_must_be_positive_and_finite(timeout):
    with pytest.raises(ValueError):
        BankIDClient(request_timeout=timeout)
    with pytest.raises(ValueError):
        BankIDClient(attempt_timeout=timeout)
