"""Explicit read-only account output contracts."""

from pydantic import BaseModel, ConfigDict


class PrivateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Money(PrivateModel):
    amount: str
    currency: str


class Account(PrivateModel):
    account_id: str
    name: str
    account_type: str
    hidden: bool
    total_value: Money | None = None
    balance: Money | None = None
    currency_balances: list[Money]


class Accounts(PrivateModel):
    accounts: list[Account]


class Instrument(PrivateModel):
    instrument_id: str | None = None
    order_book_id: str | None = None
    isin: str | None = None
    name: str
    instrument_type: str
    currency: str | None = None


class Holding(PrivateModel):
    account_id: str
    position_id: str
    instrument: Instrument
    volume: str
    market_value: Money | None = None
    acquired_value: Money | None = None
    average_acquired_price: Money | None = None
    source_updated_at: str | None = None


class CashPosition(PrivateModel):
    account_id: str
    balance: Money


class Holdings(PrivateModel):
    holdings: list[Holding]
    cash_positions: list[CashPosition]


class Transaction(PrivateModel):
    transaction_id: str
    account_id: str
    transaction_type: str
    description: str
    date: str
    settlement_date: str | None = None
    instrument_name: str | None = None
    isin: str | None = None
    order_book_id: str | None = None
    volume: str | None = None
    amount: Money | None = None
    commission: Money | None = None


class Transactions(PrivateModel):
    transactions: list[Transaction]
    returned: int
    total_reported: int
    truncated: bool
    first_transaction_date: str | None = None


class CreditBreakpoint(PrivateModel):
    interest: str | None = None
    upper_limit: str | None = None
    breakpoint_type: str | None = None


class CreditInfo(PrivateModel):
    account_id: str
    credit_limit: str | None = None
    ongoing_orders: str | None = None
    used_credit: str | None = None
    interest: str | None = None
    leverage: str | None = None
    loan_to_value: str | None = None
    collateral_value: str | None = None
    breakpoints: list[CreditBreakpoint]


class CreditInformation(PrivateModel):
    accounts: list[CreditInfo]


class Watchlist(PrivateModel):
    watchlist_id: str
    name: str
    order_book_ids: list[str]
    created_at: str | None = None
    modified_at: str | None = None


class Watchlists(PrivateModel):
    watchlists: list[Watchlist]


class PriceAlert(PrivateModel):
    alert_id: str
    account_id: str
    price: str
    valid_until: str
    direction: str
    recurring: bool
    email: bool
    notification: bool
    sms: bool


class PriceAlerts(PrivateModel):
    alerts: list[PriceAlert]


class CustomerOffer(PrivateModel):
    offer_id: str
    title: str
    offer_type: str
    last_response_date: str | None = None
    responded: bool


class CustomerOffers(PrivateModel):
    offers: list[CustomerOffer]


class PortfolioInsights(PrivateModel):
    from_date: str | None = None
    to_date: str | None = None
    start_value: str | None = None
    current_value: str | None = None
    total_change: str | None = None
    total: str | None = None
    development: str | None = None
    dividends: str | None = None
    has_unlisted_instrument: bool


class NewsArticle(PrivateModel):
    published_at: str | None = None
    headline: str
    summary: str | None = None
    source: str | None = None
    category: str | None = None
    url: str | None = None


class InstrumentNews(PrivateModel):
    articles: list[NewsArticle]
    truncated: bool


class ForumPost(PrivateModel):
    author: str
    title: str
    content: str
    likes: int | None = None
    replies: int | None = None
    timestamp: int | None = None
    url: str | None = None


class ForumPosts(PrivateModel):
    posts: list[ForumPost]
    truncated: bool


class InsiderTransaction(PrivateModel):
    order_book_id: str | None = None
    transaction_date: str
    reported_date: str | None = None
    insider_name: str
    insider_position: str | None = None
    transaction_type: str
    price: str | None = None
    quantity: str | None = None
    total_value: str | None = None
    currency: str | None = None
    market_transaction: bool


class InsiderTransactions(PrivateModel):
    transactions: list[InsiderTransaction]
    buy_count: int | None = None
    buy_total_value: str | None = None
    sell_count: int | None = None
    sell_total_value: str | None = None
    truncated: bool


class ActiveOrder(PrivateModel):
    order_id: str
    account_id: str | None = None
    order_book_id: str | None = None
    side: str | None = None
    state: str | None = None
    price: str | None = None
    volume: str | None = None
    valid_until: str | None = None


class ActiveOrders(PrivateModel):
    orders: list[ActiveOrder]
    truncated: bool


class Deal(PrivateModel):
    deal_id: str
    account_id: str | None = None
    order_id: str | None = None
    order_book_id: str | None = None
    side: str | None = None
    price: str | None = None
    volume: str | None = None
    traded_at: str | None = None


class Deals(PrivateModel):
    deals: list[Deal]
    truncated: bool


class StopLossOrder(PrivateModel):
    stop_loss_id: str
    account_id: str | None = None
    order_book_id: str | None = None
    status: str | None = None
    trigger_type: str | None = None
    trigger_value: str | None = None
    valid_until: str | None = None
    order_type: str | None = None
    price: str | None = None
    volume: str | None = None


class StopLossOrders(PrivateModel):
    orders: list[StopLossOrder]
    truncated: bool
