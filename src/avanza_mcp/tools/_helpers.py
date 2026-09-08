"""Shared read-only annotations, safe API errors, and page metadata."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp.exceptions import ToolError

from ..client.exceptions import (
    AvanzaAPIError,
    AvanzaAuthError,
    AvanzaError,
    AvanzaNetworkError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
    AvanzaRetryableError,
    AvanzaTimeoutError,
)
from ..models.contracts import AnalysisPage, PageMetadata

READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


@contextmanager
def api_errors() -> Iterator[None]:
    """Translate expected failures without logging or exposing upstream payloads."""
    try:
        yield
    except AvanzaError as exc:
        if isinstance(exc, AvanzaNotFoundError):
            message = "Avanza did not find the requested data. Check the order_book_id and instrument type."
        elif isinstance(exc, AvanzaAuthError):
            message = "Avanza denied access to this public endpoint. This tool cannot authenticate an account."
        elif isinstance(exc, AvanzaRateLimitError):
            retry = exc.retry_after
            message = "Avanza rate limit reached. " + (
                f"Retry after {retry} seconds."
                if type(retry) is int and 0 <= retry <= 86400
                else "Retry later."
            )
        elif isinstance(
            exc, (AvanzaNetworkError, AvanzaTimeoutError, AvanzaRetryableError)
        ) or (
            isinstance(exc, AvanzaAPIError)
            and type(exc.status_code) is int
            and 500 <= exc.status_code <= 599
        ):
            message = "Avanza is temporarily unavailable. Retry later."
        else:
            message = "Avanza could not provide the requested data."
        raise ToolError(message) from exc


def page_metadata(total: int | None, offset: int, limit: int) -> PageMetadata:
    return PageMetadata(
        offset=offset,
        limit=limit,
        total=total,
        returned=min(limit, max(0, total - offset)) if total is not None else 0,
        has_more=total is not None and offset + limit < total,
    )


def analysis_page(
    analysis: dict, selection: str, metric: str, offset: int, limit: int
) -> AnalysisPage:
    section = analysis.get(selection)
    records = section.get(metric) if section is not None else None
    data = {}
    if selection in analysis:
        data[selection] = None if section is None else {}
        if section is not None and metric in section:
            data[selection][metric] = (
                records[offset : offset + limit] if records is not None else None
            )
    return AnalysisPage(
        selection=selection,
        metric=metric,
        available_metrics=list(section) if section is not None else [],
        data=data,
        pagination=page_metadata(
            len(records) if records is not None else None, offset, limit
        ),
    )
