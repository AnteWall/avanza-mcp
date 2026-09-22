"""Synthetic fixed-endpoint account read tests."""

import re
from contextlib import asynccontextmanager
from datetime import date

import httpx
import pytest
import respx

from avanza_mcp.client import AvanzaClient
from avanza_mcp.client.accounts import AccountAuthExpired, AccountClient
from avanza_mcp.client.bankid import SessionMaterial


@asynccontextmanager
async def client():
    session = SessionMaterial((), "token")
    async with AvanzaClient(session_provider=lambda: session) as base_client:
        yield AccountClient(base_client)


def mock_avanza(handler):
    return respx.route(
        url__regex=re.compile(r"https://www\.avanza\.se/.*")
    ).mock(side_effect=handler)


@respx.mock
async def test_accounts_holdings_and_transactions_are_explicit_and_bounded():
    requests = []

    async def handler(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.headers["x-securitytoken"] == "token"
        if request.url.path.endswith("categorizedAccounts"):
            return httpx.Response(
                200,
                json={
                    "accounts": [
                        {
                            "id": 1,
                            "urlParameterId": "isk-1",
                            "name": {"defaultName": "ISK"},
                            "type": "INVESTMENT_SAVINGS_ACCOUNT",
                            "balance": {"value": "10.00", "unit": "SEK"},
                            "currencyBalances": [],
                            "personalNumber": "must-not-leak",
                        }
                    ]
                },
            )
        if request.url.path.endswith("positions"):
            return httpx.Response(
                200,
                json={
                    "withOrderbook": [
                        {
                            "id": "p1",
                            "account": {"id": 1},
                            "instrument": {
                                "id": 2,
                                "name": "Synthetic",
                                "type": "STOCK",
                                "currency": "SEK",
                                "orderbook": {
                                    "id": 3,
                                    "quote": {"updated": "2026-01-01"},
                                },
                            },
                            "volume": {"value": "2"},
                            "value": {"value": "20", "unit": "SEK"},
                        }
                    ],
                    "withoutOrderbook": [],
                    "cashPositions": [
                        {
                            "account": {"id": 1},
                            "totalBalance": {"value": "10", "unit": "SEK"},
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "transactions": [
                    {
                        "id": "t1",
                        "account": {"id": 1},
                        "type": "DIVIDEND",
                        "description": "Synthetic dividend",
                        "date": "2026-01-01",
                        "amount": {"value": "5", "unit": "SEK"},
                        "noteId": "must-not-leak",
                    }
                ],
                "transactionsAfterFiltering": 2,
                "firstTransactionDate": "2020-01-01",
            },
        )

    mock_avanza(handler)
    async with client() as account_client:
        accounts = await account_client.accounts()
        holdings = await account_client.holdings()
        transactions = await account_client.transactions(
            from_date=date(2026, 1, 1), to_date=date(2026, 1, 31), limit=1
        )

    assert accounts.accounts[0].balance.amount == "10.00"
    assert holdings.holdings[0].instrument.order_book_id == "3"
    assert holdings.cash_positions[0].balance.amount == "10"
    assert transactions.returned == 1 and transactions.truncated is True
    assert dict(requests[-1].url.params) == {
        "maxElements": "1",
        "from": "2026-01-01",
        "to": "2026-01-31",
    }
    output = accounts.model_dump_json() + transactions.model_dump_json()
    assert "personalNumber" not in output and "noteId" not in output


@respx.mock
async def test_confirmed_unauthorized_is_distinct():
    async def handler(request):
        return httpx.Response(401, json={"secret": "not exposed"})

    mock_avanza(handler)
    async with client() as account_client:
        with pytest.raises(AccountAuthExpired):
            await account_client.accounts()


@respx.mock
async def test_additional_private_reads_use_fixed_routes_and_explicit_projections():
    requests = []

    async def handler(request):
        requests.append(request)
        path = request.url.path
        if path.endswith("/credited"):
            return httpx.Response(
                200,
                json={
                    "creditInfos": [
                        {
                            "accountId": "a1",
                            "creditLimit": 100,
                            "currentUsedCredit": 10,
                            "currentCreditBreakPoints": [
                                {"interest": 1.5, "upperLimit": 100, "type": "NORMAL"}
                            ],
                            "personalNumber": "must-not-leak",
                        }
                    ]
                },
            )
        if path.endswith("/watchlist"):
            return httpx.Response(
                200,
                json=[
                    {
                        "watchListId": "w1",
                        "customerId": {"id": 999},
                        "orderbookIds": ["123"],
                        "name": "Mine",
                        "created": "2026-01-01",
                        "modified": "2026-01-02",
                    }
                ],
            )
        if "/alert/" in path:
            return httpx.Response(
                200,
                json=[
                    {
                        "alertId": "p1",
                        "accountId": "a1",
                        "price": 12.5,
                        "validUntil": "2026-12-31",
                        "direction": "ABOVE",
                        "recurring": False,
                        "email": False,
                        "notification": True,
                        "sms": False,
                    }
                ],
            )
        if path.endswith("/currentoffers/"):
            return httpx.Response(
                200,
                json=[
                    {
                        "customerOfferId": "o1",
                        "title": "Offer",
                        "type": "INFO",
                        "lastResponseDate": "2026-01-01",
                        "hasResponded": False,
                    }
                ],
            )
        if path.endswith("/insights"):
            return httpx.Response(
                200,
                json={
                    "fromDate": "2026-01-01",
                    "toDate": "2026-01-31",
                    "developmentResponse": {
                        "totalOutcome": {
                            "total": 110,
                            "development": 10,
                            "dividends": 2,
                        },
                        "hasUnlistedInstrument": False,
                        "positions": [{"secret": "must-not-leak"}],
                    },
                    "totalDevelopment": {
                        "startValue": 100,
                        "currentValue": 110,
                        "totalChange": 10,
                    },
                },
            )
        if path.endswith("/news/123"):
            return httpx.Response(
                200,
                json={
                    "articles": [
                        {
                            "timePublished": "2026-01-01",
                            "headline": f"Article {index}",
                            "intro": "Summary",
                            "newsSource": "Source",
                            "fullArticleLink": "/article",
                            "trackingId": "must-not-leak",
                        }
                        for index in range(2)
                    ]
                },
            )
        if path.endswith("/forum/123"):
            return httpx.Response(
                200,
                json={
                    "posts": [
                        {
                            "author": "Person",
                            "title": "Title",
                            "content": "Content",
                            "likes": 1,
                            "replies": 2,
                            "timestamp": 3,
                            "url": "/post",
                        }
                    ]
                },
            )
        if path.endswith("/transactions/123"):
            return httpx.Response(
                200,
                json={
                    "transactions": [
                        {
                            "orderbookId": "123",
                            "transactionDate": "2026-01-01",
                            "reportedDate": "2026-01-02",
                            "insiderName": "Person",
                            "transactionType": "BUY",
                            "price": 10,
                            "quantity": 2,
                            "totalValue": 20,
                            "currency": "SEK",
                            "marketTransaction": True,
                        }
                    ],
                    "buyCount": 1,
                    "buyTotalValue": 20,
                    "sellCount": 0,
                    "sellTotalValue": 0,
                },
            )
        if path.endswith("/orders"):
            return httpx.Response(
                200,
                json={
                    "orders": [
                        {
                            "orderId": "order-1",
                            "accountId": "a1",
                            "orderbookId": "123",
                            "side": "BUY",
                            "state": "ACTIVE",
                            "price": 10,
                            "volume": 2,
                            "modifiable": True,
                        }
                    ]
                },
            )
        if path.endswith("/deals"):
            return httpx.Response(
                200,
                json={
                    "deals": [
                        {
                            "dealId": "deal-1",
                            "account": {"id": "a1"},
                            "orderbook": {"id": "123"},
                            "side": "BUY",
                            "price": 10,
                            "volume": 2,
                        }
                    ]
                },
            )
        if path.endswith("/stoploss"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "stop-1",
                        "status": "ACTIVE",
                        "account": {"id": "a1"},
                        "orderbook": {"id": "123"},
                        "trigger": {"type": "LESS_OR_EQUAL", "value": 9},
                        "order": {"type": "SELL", "price": 8, "volume": 2},
                        "editable": True,
                    }
                ],
            )
        raise AssertionError(path)

    mock_avanza(handler)
    async with client() as account_client:
        results = [
            await account_client.credit_info("credited"),
            await account_client.watchlists(),
            await account_client.price_alerts("123"),
            await account_client.offers(),
            await account_client.insights(["a1"], "THIS_YEAR"),
            await account_client.news("123", 1),
            await account_client.forum_posts("123", 1),
            await account_client.insider_transactions("123", 1),
            await account_client.active_orders(100),
            await account_client.deals(100),
            await account_client.stop_losses(100),
        ]

    insight_request = next(
        request for request in requests if request.url.path.endswith("/insights")
    )
    assert insight_request.method == "POST"
    assert insight_request.content == b'{"timePeriod":"THIS_YEAR","accountIds":["a1"]}'
    output = "".join(result.model_dump_json() for result in results)
    assert "must-not-leak" not in output
    assert "customerId" not in output
    assert "externalAccount" not in output
    assert "modifiable" not in output and "editable" not in output
