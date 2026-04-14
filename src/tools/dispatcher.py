"""Tool dispatcher — maps tool names to their Python implementations."""

from __future__ import annotations

import json

from src.agent.utils.logger import get_logger
from src.config import settings
from src.tools import alpaca as alpaca_tool, binance_tool, coinbase, ibkr as ibkr_tool
from src.tools.market_data import (
    get_crypto_data,
    get_earnings_calendar,
    get_market_overview,
    get_options_chain,
    get_stock_data,
    get_technical_indicators,
    search_ticker,
)
from src.tools.news import search_market_news
from src.tools.portfolio import get_account_info, get_portfolio_summary, get_trade_history
from src.tools.simulator import run_simulation

logger = get_logger(__name__)


async def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Call the appropriate tool and return a JSON string result."""
    logger.info("Tool call: %s(%s)", tool_name, json.dumps(tool_input)[:200])
    try:
        result = await _dispatch(tool_name, tool_input)
    except Exception as exc:
        logger.exception("Tool %s raised an exception", tool_name)
        result = {"error": str(exc), "tool": tool_name}
    return json.dumps(result, default=str, ensure_ascii=False)


async def _dispatch(name: str, inp: dict) -> object:  # noqa: PLR0911, PLR0912
    # ── Market Data ────────────────────────────────────────────────────────────
    if name == "get_stock_data":
        return get_stock_data(**inp)
    if name == "get_crypto_data":
        return get_crypto_data(**inp)
    if name == "get_market_overview":
        return get_market_overview()
    if name == "get_technical_indicators":
        return get_technical_indicators(**inp)
    if name == "get_options_chain":
        return get_options_chain(**inp)
    if name == "search_ticker":
        return search_ticker(**inp)
    if name == "get_earnings_calendar":
        return get_earnings_calendar(**inp)

    # ── News ───────────────────────────────────────────────────────────────────
    if name == "search_market_news":
        return search_market_news(**inp)

    # ── Portfolio ──────────────────────────────────────────────────────────────
    if name == "get_portfolio_summary":
        return get_portfolio_summary(broker=inp.get("broker"))
    if name == "get_account_info":
        return get_account_info(broker=inp["broker"])
    if name == "get_trade_history":
        return get_trade_history(broker=inp["broker"], days=inp.get("days", 30))

    # ── Trade Execution ────────────────────────────────────────────────────────
    if name == "execute_trade":
        return await _execute_trade(inp)
    if name == "cancel_order":
        return _cancel_order(inp)

    # ── Simulation ─────────────────────────────────────────────────────────────
    if name == "run_simulation":
        return run_simulation(**inp)

    # ── Agent Control ──────────────────────────────────────────────────────────
    if name == "set_trading_mode":
        return _set_trading_mode(inp["mode"])
    if name == "generate_report":
        return await _generate_report(inp)

    return {"error": f"Unknown tool: {name}"}


async def _execute_trade(inp: dict) -> dict:
    broker = inp["broker"]
    symbol = inp["symbol"]
    side = inp["side"]
    quantity = float(inp["quantity"])
    order_type = inp.get("order_type", "market")
    limit_price = inp.get("limit_price")
    stop_price = inp.get("stop_price")
    reason = inp.get("reason", "")

    # Safety check for auto mode
    if settings.trading_mode == "auto":
        if (
            settings.auto_allowed_symbols_set
            and symbol.upper() not in settings.auto_allowed_symbols_set
        ):
            return {
                "blocked": True,
                "reason": f"{symbol} is not in the auto-trading allowed symbols list.",
            }

    if settings.trading_mode == "recommend":
        return {
            "status": "pending_confirmation",
            "message": (
                f"RECOMMENDATION: {side.upper()} {quantity} {symbol} via {broker} "
                f"({order_type} order{f' @ {limit_price}' if limit_price else ''}). "
                f"Reason: {reason}. "
                "Reply 'confirm trade' to execute, or 'cancel trade' to discard."
            ),
            "trade_details": {
                "broker": broker,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "limit_price": limit_price,
                "stop_price": stop_price,
            },
        }

    # AUTO mode — execute immediately
    result = _route_order(broker, symbol, side, quantity, order_type, limit_price, stop_price)
    result["reason"] = reason

    # Persist to DB (fire-and-forget; import inline to avoid circular)
    try:
        from src.db.database import async_session
        from src.db.models import Trade

        async with async_session() as session:
            trade = Trade(
                broker=broker,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price,
                order_type=order_type,
                status=result.get("status", "submitted"),
                broker_order_id=result.get("order_id"),
                mode="auto",
                reason=reason,
            )
            session.add(trade)
            await session.commit()
    except Exception as exc:
        logger.warning("Failed to persist trade to DB: %s", exc)

    return result


def _route_order(
    broker: str,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str,
    limit_price: float | None,
    stop_price: float | None,
) -> dict:
    if broker == "alpaca":
        return alpaca_tool.submit_alpaca_order(
            symbol, side, quantity, order_type, limit_price, stop_price
        )
    if broker == "ibkr":
        return ibkr_tool.submit_ibkr_order(symbol, side, quantity, order_type, limit_price)
    if broker == "coinbase":
        return coinbase.submit_coinbase_order(symbol, side, quantity, order_type, limit_price)
    if broker == "binance":
        return binance_tool.submit_binance_order(symbol, side, quantity, order_type, limit_price)
    return {"error": f"Unknown broker: {broker}"}


def _cancel_order(inp: dict) -> dict:
    broker = inp["broker"]
    order_id = inp["order_id"]
    if broker == "alpaca":
        return alpaca_tool.cancel_alpaca_order(order_id)
    if broker == "ibkr":
        return ibkr_tool.cancel_ibkr_order(order_id)
    if broker == "coinbase":
        return coinbase.cancel_coinbase_order(order_id)
    if broker == "binance":
        return binance_tool.cancel_binance_order(order_id)
    return {"error": f"Unknown broker: {broker}"}


def _set_trading_mode(mode: str) -> dict:
    if mode not in ("recommend", "auto"):
        return {"error": "mode must be 'recommend' or 'auto'"}
    # Mutate the settings singleton for the running process
    settings.trading_mode = mode  # type: ignore[misc]
    return {
        "success": True,
        "trading_mode": mode,
        "message": f"Trading mode switched to '{mode}'.",
    }


async def _generate_report(inp: dict) -> dict:
    from src.scheduler.reporter import generate_report

    return await generate_report(
        period_start=inp["period_start"],
        period_end=inp.get("period_end"),
    )
