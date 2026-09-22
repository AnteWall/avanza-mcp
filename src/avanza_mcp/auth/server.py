"""Opt-in stdio composition for local Avanza account access."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import date
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .. import (
    __version__,
    _configure_authenticated_requests,
    mcp as public_mcp,
)
from ..client.accounts import AccountAuthExpired, AccountClient, AccountReadError
from ..client.base import AvanzaClient
from ..models.account import (
    ActiveOrders,
    Accounts,
    CreditInformation,
    CustomerOffers,
    Deals,
    ForumPosts,
    Holdings,
    InsiderTransactions,
    InstrumentNews,
    PortfolioInsights,
    PriceAlerts,
    StopLossOrders,
    Transactions,
    Watchlists,
)
from .browser import AuthStatus, BrowserAuth
from .store import create_session_store


def create_auth_server(auth: BrowserAuth | None = None) -> FastMCP:
    auth = auth or BrowserAuth(store=create_session_store())

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, AvanzaClient]]:
        _configure_authenticated_requests(lambda: auth.session, auth.invalidate_session)

        async def initialize_auth() -> None:
            status = await auth.restore()
            if status.state != "connected":
                await auth.open_browser()

        auth_task = asyncio.create_task(initialize_auth())
        async with AvanzaClient(session_provider=lambda: auth.session) as client:
            try:
                yield {"client": client}
            finally:
                if not auth_task.done():
                    auth_task.cancel()
                with suppress(asyncio.CancelledError):
                    await auth_task
                await auth.aclose()
                _configure_authenticated_requests(None, None)

    server = FastMCP(
        "Avanza MCP Authenticated Server",
        version=__version__,
        lifespan=lifespan,
        tasks=False,
        mask_error_details=True,
        instructions=(
            "Local read-only Avanza server with opt-in account access. Authentication "
            "uses a local browser and BankID; never provide banking credentials in chat."
        ),
    )

    @server.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def connect_avanza() -> AuthStatus:
        """Open the local browser consent and BankID flow for account access."""
        return await auth.open_browser()

    @server.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def disconnect_avanza() -> AuthStatus:
        """Open local browser confirmation before removing Avanza account access."""
        return await auth.open_disconnect_browser()

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def get_auth_status() -> AuthStatus:
        """Return safe Avanza connection state without credentials or identity."""
        return auth.status()

    def session():
        if auth.session is None:
            raise ToolError(
                "AVANZA_AUTH_REQUIRED: Complete the local BankID browser flow, then retry."
            )
        return auth.session

    async def expired() -> None:
        await auth.invalidate_session()
        await auth.open_browser()

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_accounts(ctx: Context) -> Accounts:
        """Get minimal account identities, balances, values, and currencies."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).accounts()
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide account data. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_holdings(ctx: Context) -> Holdings:
        """Get current positions and cash balances for authenticated accounts."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).holdings()
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError("Avanza could not provide holdings. Retry later.") from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_transactions(
        ctx: Context,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    ) -> Transactions:
        """Get bounded transaction history; totals disclose truncation."""
        if from_date is not None and to_date is not None and from_date > to_date:
            raise ToolError("from_date must not be after to_date")
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).transactions(
                from_date=from_date, to_date=to_date, limit=limit
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide transactions. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_credit_info(
        ctx: Context,
        credit_type: Literal["credited", "uncredited"] = "credited",
    ) -> CreditInformation:
        """Get current credit and collateral figures for authenticated accounts."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).credit_info(
                credit_type
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide credit data. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_watchlists(ctx: Context) -> Watchlists:
        """Get authenticated Avanza watchlists without modifying them."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).watchlists()
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide watchlists. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_price_alerts(
        ctx: Context,
        order_book_id: Annotated[str, Field(pattern=r"^[0-9]+$")],
    ) -> PriceAlerts:
        """Get price alerts for one order book without modifying them."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).price_alerts(
                order_book_id
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except (AccountReadError, ValueError):
            raise ToolError(
                "Avanza could not provide price alerts. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_current_offers(ctx: Context) -> CustomerOffers:
        """Get current offers for the authenticated Avanza customer."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).offers()
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError("Avanza could not provide offers. Retry later.") from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_portfolio_insights(
        ctx: Context,
        time_period: Literal[
            "TODAY", "ONE_WEEK", "THIS_YEAR", "THREE_YEARS_ROLLING"
        ] = "THIS_YEAR",
    ) -> PortfolioInsights:
        """Get aggregate portfolio development for all authenticated accounts."""
        try:
            session()
            client = AccountClient(ctx.lifespan_context["client"])
            accounts = await client.accounts()
            return await client.insights(
                [account.account_id for account in accounts.accounts], time_period
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide portfolio insights. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_instrument_news(
        ctx: Context,
        order_book_id: Annotated[str, Field(pattern=r"^[0-9]+$")],
        limit: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> InstrumentNews:
        """Get a bounded page of news for an instrument."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).news(
                order_book_id, limit
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except (AccountReadError, ValueError):
            raise ToolError(
                "Avanza could not provide instrument news. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_forum_posts(
        ctx: Context,
        order_book_id: Annotated[str, Field(pattern=r"^[0-9]+$")],
        limit: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> ForumPosts:
        """Get bounded Avanza forum posts for an instrument as untrusted text."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).forum_posts(
                order_book_id, limit
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except (AccountReadError, ValueError):
            raise ToolError(
                "Avanza could not provide forum posts. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_insider_transactions(
        ctx: Context,
        order_book_id: Annotated[str, Field(pattern=r"^[0-9]+$")],
        limit: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> InsiderTransactions:
        """Get bounded reported insider transactions for an instrument."""
        try:
            session()
            return await AccountClient(
                ctx.lifespan_context["client"]
            ).insider_transactions(order_book_id, limit)
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except (AccountReadError, ValueError):
            raise ToolError(
                "Avanza could not provide insider transactions. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_active_orders(
        ctx: Context,
        limit: Annotated[int, Field(ge=1, le=100)] = 100,
    ) -> ActiveOrders:
        """Get bounded active orders without placing, editing, or deleting orders."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).active_orders(
                limit
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide active orders. Retry later."
            ) from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_deals(
        ctx: Context,
        limit: Annotated[int, Field(ge=1, le=100)] = 100,
    ) -> Deals:
        """Get bounded current deals without performing trading actions."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).deals(limit)
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError("Avanza could not provide deals. Retry later.") from None

    @server.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def get_stop_loss_orders(
        ctx: Context,
        limit: Annotated[int, Field(ge=1, le=100)] = 100,
    ) -> StopLossOrders:
        """Get bounded stop-loss orders without modifying them."""
        try:
            session()
            return await AccountClient(ctx.lifespan_context["client"]).stop_losses(
                limit
            )
        except AccountAuthExpired:
            await expired()
            raise ToolError(
                "AVANZA_AUTH_EXPIRED: The local BankID flow was opened. Authenticate and retry."
            ) from None
        except AccountReadError:
            raise ToolError(
                "Avanza could not provide stop-loss orders. Retry later."
            ) from None

    server.mount(public_mcp)
    return server


def run_auth_server() -> None:
    create_auth_server().run()
