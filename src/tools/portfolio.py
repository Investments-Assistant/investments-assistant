"""Portfolio aggregator — combines holdings across all brokers."""

from __future__ import annotations

import yfinance as yf

from src.agent.utils.logger import get_logger
from src.tools import alpaca as alpaca_tool, binance_tool, coinbase, ibkr as ibkr_tool

logger = get_logger(__name__)


def _enrich_position(pos: dict, symbol_key: str = "symbol") -> dict:
    """Add current market price to a position if not already present."""
    sym = pos.get(symbol_key)
    if not sym or pos.get("current_price"):
        return pos
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info or {}
        pos["current_price"] = info.get("regularMarketPrice") or info.get("currentPrice")
    except Exception:
        pass
    return pos


def get_portfolio_summary(broker: str | None = None) -> dict:
    """Aggregate positions across all (or a specific) broker."""
    result: dict[str, object] = {
        "positions": [],
        "accounts": [],
        "total_market_value_usd": 0.0,
        "total_unrealized_pnl_usd": 0.0,
    }

    def _collect(name: str, positions_fn, account_fn) -> None:
        try:
            acc = account_fn()
            if "error" not in acc:
                result["accounts"].append(acc)  # type: ignore[attr-defined]
            positions = positions_fn()
            for p in positions:
                if "error" not in p:
                    p["broker"] = name
                    result["positions"].append(p)  # type: ignore[attr-defined]
                    mv = p.get("market_value") or 0
                    upnl = p.get("unrealized_pnl") or p.get("unrealized_pl") or 0
                    result["total_market_value_usd"] = (  # type: ignore[operator]
                        float(result["total_market_value_usd"]) + float(mv)
                    )
                    result["total_unrealized_pnl_usd"] = (  # type: ignore[operator]
                        float(result["total_unrealized_pnl_usd"]) + float(upnl)
                    )
        except Exception as exc:
            logger.warning("%s portfolio fetch failed: %s", name, exc)

    if broker is None or broker == "alpaca":
        _collect("alpaca", alpaca_tool.get_alpaca_positions, alpaca_tool.get_alpaca_account)
    if broker is None or broker == "ibkr":
        _collect("ibkr", ibkr_tool.get_ibkr_positions, ibkr_tool.get_ibkr_account)
    if broker is None or broker == "coinbase":
        _collect(
            "coinbase",
            coinbase.get_coinbase_positions,
            coinbase.get_coinbase_account,
        )
    if broker is None or broker == "binance":
        _collect(
            "binance",
            binance_tool.get_binance_positions,
            binance_tool.get_binance_account,
        )

    result["total_market_value_usd"] = round(float(result["total_market_value_usd"]), 2)  # type: ignore[arg-type]
    result["total_unrealized_pnl_usd"] = round(float(result["total_unrealized_pnl_usd"]), 2)  # type: ignore[arg-type]
    return result


def get_account_info(broker: str) -> dict:
    dispatch = {
        "alpaca": alpaca_tool.get_alpaca_account,
        "ibkr": ibkr_tool.get_ibkr_account,
        "coinbase": coinbase.get_coinbase_account,
        "binance": binance_tool.get_binance_account,
    }
    fn = dispatch.get(broker)
    if not fn:
        return {"error": f"Unknown broker: {broker}"}
    return fn()


def get_trade_history(broker: str, days: int = 30) -> list[dict]:
    dispatch = {
        "alpaca": lambda: alpaca_tool.get_alpaca_orders(days),
        "ibkr": lambda: ibkr_tool.get_ibkr_orders(days),
        "coinbase": lambda: coinbase.get_coinbase_orders(days),
        "binance": lambda: binance_tool.get_binance_orders(days),
    }
    fn = dispatch.get(broker)
    if not fn:
        return [{"error": f"Unknown broker: {broker}"}]
    return fn()
