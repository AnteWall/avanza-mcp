"""Fixed-endpoint authenticated account reads with explicit projections."""

from datetime import date
from typing import Any

import httpx

from ..models.account import (
    Account,
    Accounts,
    ActiveOrder,
    ActiveOrders,
    CashPosition,
    CreditBreakpoint,
    CreditInfo,
    CreditInformation,
    CustomerOffer,
    CustomerOffers,
    Deal,
    Deals,
    ForumPost,
    ForumPosts,
    Holding,
    Holdings,
    InsiderTransaction,
    InsiderTransactions,
    InstrumentNews,
    Instrument,
    Money,
    NewsArticle,
    PortfolioInsights,
    PriceAlert,
    PriceAlerts,
    StopLossOrder,
    StopLossOrders,
    Transaction,
    Transactions,
    Watchlist,
    Watchlists,
)
from .base import AvanzaClient
from .exceptions import AvanzaAuthError

_ACCOUNTS = "/_api/account-overview/overview/categorizedAccounts"
_POSITIONS = "/_api/position-data/positions"
_TRANSACTIONS = "/_api/transactions/list"
_CREDIT_INFO = "/_api/superloan/creditinfo/{credit_type}"
_WATCHLISTS = "/_api/watchlist/watchlist"
_PRICE_ALERTS = "/_cqbe/marketing/service/alert/{order_book_id}"
_OFFERS = "/_api/customer-offer/currentoffers/"
_INSIGHTS = "/_api/insights-development/insights"
_NEWS = "/_api/market-guide/news/{order_book_id}"
_FORUM = "/_api/market-guide/forum/{order_book_id}"
_INSIDER_TRANSACTIONS = "/_api/market-insider-transactions/transactions/{order_book_id}"
_DEALS = "/_api/trading/rest/deals"
_ORDERS = "/_api/trading/rest/orders"
_STOP_LOSSES = "/_api/trading/stoploss"


class AccountAuthExpired(RuntimeError):
    pass


class AccountReadError(RuntimeError):
    pass


class AccountClient:
    def __init__(self, client: AvanzaClient) -> None:
        self._client = client

    async def accounts(self) -> Accounts:
        body = await self._get(_ACCOUNTS)
        records = body.get("accounts")
        if not isinstance(records, list):
            raise AccountReadError
        return Accounts(accounts=[self._account(item) for item in records])

    async def holdings(self) -> Holdings:
        body = await self._get(_POSITIONS)
        positions = []
        for key in ("withOrderbook", "withoutOrderbook"):
            values = body.get(key, [])
            if not isinstance(values, list):
                raise AccountReadError
            positions.extend(self._holding(item) for item in values)
        cash = body.get("cashPositions", [])
        if not isinstance(cash, list):
            raise AccountReadError
        return Holdings(
            holdings=positions,
            cash_positions=[self._cash(item) for item in cash],
        )

    async def transactions(
        self, *, from_date: date | None, to_date: date | None, limit: int
    ) -> Transactions:
        params: dict[str, str | int] = {"maxElements": limit}
        if from_date is not None:
            params["from"] = from_date.isoformat()
        if to_date is not None:
            params["to"] = to_date.isoformat()
        body = await self._get(_TRANSACTIONS, params=params)
        values = body.get("transactions")
        total = body.get("transactionsAfterFiltering")
        if not isinstance(values, list) or not isinstance(total, int):
            raise AccountReadError
        items = [self._transaction(item) for item in values[:limit]]
        first = body.get("firstTransactionDate")
        return Transactions(
            transactions=items,
            returned=len(items),
            total_reported=total,
            truncated=total > len(items),
            first_transaction_date=first if isinstance(first, str) else None,
        )

    async def credit_info(self, credit_type: str) -> CreditInformation:
        body = await self._get(_CREDIT_INFO.format(credit_type=credit_type))
        values = self._items(body, "creditInfos")
        return CreditInformation(
            accounts=[
                CreditInfo(
                    account_id=self._identifier(item.get("accountId")),
                    credit_limit=self._decimal(item.get("creditLimit")),
                    ongoing_orders=self._decimal(item.get("ongoingOrders")),
                    used_credit=self._decimal(item.get("currentUsedCredit")),
                    interest=self._decimal(item.get("currentInterest")),
                    leverage=self._decimal(item.get("currentLeverage")),
                    loan_to_value=self._decimal(item.get("currentLtv")),
                    collateral_value=self._decimal(
                        item.get("currentTotalPotentialCollateralValue")
                    ),
                    breakpoints=[
                        CreditBreakpoint(
                            interest=self._decimal(point.get("interest")),
                            upper_limit=self._decimal(point.get("upperLimit")),
                            breakpoint_type=self._optional_string(point.get("type")),
                        )
                        for point in self._dicts(
                            item.get("currentCreditBreakPoints", [])
                        )
                    ],
                )
                for item in values
            ]
        )

    async def watchlists(self) -> Watchlists:
        values = await self._get_list(_WATCHLISTS)
        return Watchlists(
            watchlists=[
                Watchlist(
                    watchlist_id=self._identifier(item.get("watchListId")),
                    name=str(item.get("name") or "Unnamed watchlist"),
                    order_book_ids=[
                        self._identifier(value)
                        for value in item.get("orderbookIds", [])
                    ],
                    created_at=self._optional_string(item.get("created")),
                    modified_at=self._optional_string(item.get("modified")),
                )
                for item in self._dicts(values)
            ]
        )

    async def price_alerts(self, order_book_id: str) -> PriceAlerts:
        if not order_book_id.isascii() or not order_book_id.isdecimal():
            raise ValueError("order_book_id must contain only ASCII numeric digits")
        values = await self._get_list(_PRICE_ALERTS.format(order_book_id=order_book_id))
        return PriceAlerts(
            alerts=[
                PriceAlert(
                    alert_id=self._identifier(item.get("alertId")),
                    account_id=self._identifier(item.get("accountId")),
                    price=self._decimal(item.get("price"), required=True),
                    valid_until=str(item.get("validUntil") or ""),
                    direction=str(item.get("direction") or "UNKNOWN"),
                    recurring=bool(item.get("recurring", False)),
                    email=bool(item.get("email", False)),
                    notification=bool(item.get("notification", False)),
                    sms=bool(item.get("sms", False)),
                )
                for item in self._dicts(values)
            ]
        )

    async def offers(self) -> CustomerOffers:
        values = await self._get_list(_OFFERS)
        return CustomerOffers(
            offers=[
                CustomerOffer(
                    offer_id=self._identifier(item.get("customerOfferId")),
                    title=str(item.get("title") or "Untitled offer"),
                    offer_type=str(item.get("type") or "UNKNOWN"),
                    last_response_date=self._optional_string(
                        item.get("lastResponseDate")
                    ),
                    responded=bool(item.get("hasResponded", False)),
                )
                for item in self._dicts(values)
            ]
        )

    async def insights(
        self, account_ids: list[str], time_period: str
    ) -> PortfolioInsights:
        body = await self._post(
            _INSIGHTS,
            json={"timePeriod": time_period, "accountIds": account_ids},
        )
        development = self._mapping(body.get("developmentResponse"))
        outcome = self._mapping(development.get("totalOutcome"))
        totals = self._mapping(body.get("totalDevelopment"))
        return PortfolioInsights(
            from_date=self._optional_string(body.get("fromDate")),
            to_date=self._optional_string(body.get("toDate")),
            start_value=self._decimal(totals.get("startValue")),
            current_value=self._decimal(totals.get("currentValue")),
            total_change=self._decimal(totals.get("totalChange")),
            total=self._decimal(outcome.get("total")),
            development=self._decimal(outcome.get("development")),
            dividends=self._decimal(outcome.get("dividends")),
            has_unlisted_instrument=bool(
                development.get("hasUnlistedInstrument", False)
            ),
        )

    async def news(self, order_book_id: str, limit: int) -> InstrumentNews:
        body = await self._instrument_get(_NEWS, order_book_id)
        values = self._items(body, "articles")
        return InstrumentNews(
            articles=[
                NewsArticle(
                    published_at=self._optional_string(item.get("timePublished")),
                    headline=str(item.get("headline") or "Untitled article"),
                    summary=self._optional_string(
                        item.get("intro") or item.get("vignette")
                    ),
                    source=self._optional_string(item.get("newsSource")),
                    category=self._optional_string(item.get("category")),
                    url=self._optional_string(item.get("fullArticleLink")),
                )
                for item in values[:limit]
            ],
            truncated=len(values) > limit,
        )

    async def forum_posts(self, order_book_id: str, limit: int) -> ForumPosts:
        body = await self._instrument_get(_FORUM, order_book_id)
        values = self._items(body, "posts") if body.get("posts") is not None else []
        return ForumPosts(
            posts=[
                ForumPost(
                    author=str(item.get("author") or "Unknown author"),
                    title=str(item.get("title") or "Untitled post"),
                    content=str(item.get("content") or ""),
                    likes=self._optional_int(item.get("likes")),
                    replies=self._optional_int(item.get("replies")),
                    timestamp=self._optional_int(item.get("timestamp")),
                    url=self._optional_string(item.get("url")),
                )
                for item in values[:limit]
            ],
            truncated=len(values) > limit,
        )

    async def insider_transactions(
        self, order_book_id: str, limit: int
    ) -> InsiderTransactions:
        body = await self._instrument_get(_INSIDER_TRANSACTIONS, order_book_id)
        values = self._items(body, "transactions")
        return InsiderTransactions(
            transactions=[
                InsiderTransaction(
                    order_book_id=self._optional_identifier(item.get("orderbookId")),
                    transaction_date=str(item.get("transactionDate") or ""),
                    reported_date=self._optional_string(item.get("reportedDate")),
                    insider_name=str(item.get("insiderName") or "Unknown insider"),
                    insider_position=self._optional_string(item.get("insiderPosition")),
                    transaction_type=str(item.get("transactionType") or "UNKNOWN"),
                    price=self._decimal(item.get("price")),
                    quantity=self._decimal(item.get("quantity")),
                    total_value=self._decimal(item.get("totalValue")),
                    currency=self._optional_string(item.get("currency")),
                    market_transaction=bool(item.get("marketTransaction", False)),
                )
                for item in values[:limit]
            ],
            buy_count=self._optional_int(body.get("buyCount")),
            buy_total_value=self._decimal(body.get("buyTotalValue")),
            sell_count=self._optional_int(body.get("sellCount")),
            sell_total_value=self._decimal(body.get("sellTotalValue")),
            truncated=len(values) > limit,
        )

    async def active_orders(self, limit: int) -> ActiveOrders:
        body = await self._get(_ORDERS)
        values = self._items(body, "orders")
        return ActiveOrders(
            orders=[self._active_order(item) for item in values[:limit]],
            truncated=len(values) > limit,
        )

    async def deals(self, limit: int) -> Deals:
        body = await self._get(_DEALS)
        values = self._items(body, "deals")
        return Deals(
            deals=[self._deal(item) for item in values[:limit]],
            truncated=len(values) > limit,
        )

    async def stop_losses(self, limit: int) -> StopLossOrders:
        values = await self._get_list(_STOP_LOSSES)
        return StopLossOrders(
            orders=[self._stop_loss(item) for item in self._dicts(values)[:limit]],
            truncated=len(values) > limit,
        )

    async def _instrument_get(
        self, template: str, order_book_id: str
    ) -> dict[str, Any]:
        if not order_book_id.isascii() or not order_book_id.isdecimal():
            raise ValueError("order_book_id must contain only ASCII numeric digits")
        return await self._get(template.format(order_book_id=order_book_id))

    async def _get(self, path: str, **kwargs) -> dict[str, Any]:
        body = await self._request("GET", path, **kwargs)
        if not isinstance(body, dict):
            raise AccountReadError
        return body

    async def _get_list(self, path: str, **kwargs) -> list[Any]:
        body = await self._request("GET", path, **kwargs)
        if not isinstance(body, list):
            raise AccountReadError
        return body

    async def _post(self, path: str, **kwargs) -> dict[str, Any]:
        body = await self._request("POST", path, **kwargs)
        if not isinstance(body, dict):
            raise AccountReadError
        return body

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            response = await self._client.request_authenticated(method, path, **kwargs)
        except AvanzaAuthError:
            raise AccountAuthExpired from None
        except httpx.TransportError:
            raise AccountReadError("network") from None
        if response.status_code == 401:
            raise AccountAuthExpired
        if response.status_code != 200:
            raise AccountReadError(f"http_{response.status_code}")
        if len(response.content) > 2 * 1024 * 1024:
            raise AccountReadError("response_too_large")
        try:
            body = response.json()
        except ValueError:
            raise AccountReadError("invalid_json") from None
        return body

    @classmethod
    def _active_order(cls, item: dict[str, Any]) -> ActiveOrder:
        return ActiveOrder(
            order_id=cls._identifier(item.get("orderId") or item.get("id")),
            account_id=cls._nested_identifier(item, "accountId", "account"),
            order_book_id=cls._nested_identifier(item, "orderbookId", "orderbook"),
            side=cls._optional_string(item.get("side")),
            state=cls._optional_string(item.get("state")),
            price=cls._decimal(item.get("price")),
            volume=cls._decimal(item.get("volume") or item.get("openVolume")),
            valid_until=cls._optional_string(item.get("validUntil")),
        )

    @classmethod
    def _deal(cls, item: dict[str, Any]) -> Deal:
        return Deal(
            deal_id=cls._identifier(item.get("dealId") or item.get("id")),
            account_id=cls._nested_identifier(item, "accountId", "account"),
            order_id=cls._optional_identifier(item.get("orderId")),
            order_book_id=cls._nested_identifier(item, "orderbookId", "orderbook"),
            side=cls._optional_string(item.get("side")),
            price=cls._decimal(item.get("price")),
            volume=cls._decimal(item.get("volume")),
            traded_at=cls._optional_string(
                item.get("tradeDate") or item.get("transactionDate")
            ),
        )

    @classmethod
    def _stop_loss(cls, item: dict[str, Any]) -> StopLossOrder:
        account = cls._mapping(item.get("account", {}))
        orderbook = cls._mapping(item.get("orderbook", {}))
        trigger = cls._mapping(item.get("trigger", {}))
        order = cls._mapping(item.get("order", {}))
        return StopLossOrder(
            stop_loss_id=cls._identifier(item.get("id")),
            account_id=cls._optional_identifier(account.get("id")),
            order_book_id=cls._optional_identifier(orderbook.get("id")),
            status=cls._optional_string(item.get("status")),
            trigger_type=cls._optional_string(trigger.get("type")),
            trigger_value=cls._decimal(trigger.get("value")),
            valid_until=cls._optional_string(trigger.get("validUntil")),
            order_type=cls._optional_string(order.get("type")),
            price=cls._decimal(order.get("price")),
            volume=cls._decimal(order.get("volume")),
        )

    @classmethod
    def _nested_identifier(
        cls, item: dict[str, Any], direct_key: str, nested_key: str
    ) -> str | None:
        value = item.get(direct_key)
        nested = item.get(nested_key)
        if value is None and isinstance(nested, dict):
            value = nested.get("id")
        return cls._optional_identifier(value)

    @classmethod
    def _items(cls, body: dict[str, Any], key: str) -> list[dict[str, Any]]:
        return cls._dicts(body.get(key, []))

    @staticmethod
    def _dicts(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not all(
            isinstance(item, dict) for item in value
        ):
            raise AccountReadError
        return value

    @staticmethod
    def _mapping(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise AccountReadError
        return value

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return value if isinstance(value, str) else None

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @classmethod
    def _account(cls, value: Any) -> Account:
        if not isinstance(value, dict):
            raise AccountReadError
        name = value.get("name", {})
        balances = value.get("currencyBalances", [])
        if not isinstance(name, dict) or not isinstance(balances, list):
            raise AccountReadError
        return Account(
            account_id=cls._identifier(value.get("id")),
            name=name.get("userDefinedName")
            or name.get("defaultName")
            or "Unknown account",
            account_type=str(value.get("type") or "UNKNOWN"),
            hidden=bool(value.get("settings", {}).get("IS_HIDDEN", False)),
            total_value=cls._money(value.get("totalValue")),
            balance=cls._money(value.get("balance")),
            currency_balances=[
                money
                for item in balances
                if (money := cls._money(item.get("balance", item)))
            ],
        )

    @classmethod
    def _holding(cls, value: Any) -> Holding:
        if not isinstance(value, dict):
            raise AccountReadError
        instrument = value.get("instrument", {})
        account = value.get("account", {})
        if not isinstance(instrument, dict) or not isinstance(account, dict):
            raise AccountReadError
        orderbook = instrument.get("orderbook") or {}
        if not isinstance(orderbook, dict):
            raise AccountReadError
        currency = instrument.get("currency")
        return Holding(
            account_id=cls._identifier(account.get("id")),
            position_id=cls._identifier(value.get("id")),
            instrument=Instrument(
                instrument_id=cls._optional_identifier(instrument.get("id")),
                order_book_id=cls._optional_identifier(orderbook.get("id")),
                isin=instrument.get("isin")
                if isinstance(instrument.get("isin"), str)
                else None,
                name=str(instrument.get("name") or "Unknown instrument"),
                instrument_type=str(instrument.get("type") or "UNKNOWN"),
                currency=currency if isinstance(currency, str) else None,
            ),
            volume=cls._decimal(value.get("volume"), required=True),
            market_value=cls._money(value.get("value"), currency),
            acquired_value=cls._money(value.get("acquiredValue"), currency),
            average_acquired_price=cls._money(
                value.get("averageAcquiredPrice"), currency
            ),
            source_updated_at=orderbook.get("quote", {}).get("updated"),
        )

    @classmethod
    def _cash(cls, value: Any) -> CashPosition:
        if not isinstance(value, dict) or not isinstance(value.get("account"), dict):
            raise AccountReadError
        return CashPosition(
            account_id=cls._identifier(value.get("account", {}).get("id")),
            balance=cls._money(value.get("totalBalance"), required=True),
        )

    @classmethod
    def _transaction(cls, value: Any) -> Transaction:
        if not isinstance(value, dict):
            raise AccountReadError
        account = value.get("account", {})
        orderbook = value.get("orderbook") or {}
        if not isinstance(account, dict) or not isinstance(orderbook, dict):
            raise AccountReadError
        return Transaction(
            transaction_id=cls._identifier(value.get("id")),
            account_id=cls._identifier(account.get("id")),
            transaction_type=str(value.get("type") or "UNKNOWN"),
            description=str(value.get("description") or "Unknown transaction"),
            date=str(value.get("date") or ""),
            settlement_date=value.get("settlementDate"),
            instrument_name=value.get("instrumentName"),
            isin=value.get("isin"),
            order_book_id=cls._optional_identifier(orderbook.get("id")),
            volume=cls._decimal(value.get("volume")),
            amount=cls._money(value.get("amount"), orderbook.get("currency")),
            commission=cls._money(value.get("commission"), orderbook.get("currency")),
        )

    @staticmethod
    def _identifier(value: Any) -> str:
        if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value):
            return str(value)
        raise AccountReadError

    @classmethod
    def _optional_identifier(cls, value: Any) -> str | None:
        return None if value is None else cls._identifier(value)

    @staticmethod
    def _decimal(value: Any, *, required: bool = False) -> str | None:
        if isinstance(value, dict):
            value = value.get("value")
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            return str(value)
        if required:
            raise AccountReadError
        return None

    @classmethod
    def _money(
        cls, value: Any, fallback: str | None = None, *, required: bool = False
    ) -> Money | None:
        amount = cls._decimal(value)
        if amount is None:
            if required:
                raise AccountReadError
            return None
        currency = value.get("unit") if isinstance(value, dict) else None
        return Money(amount=amount, currency=currency or fallback or "SEK")
