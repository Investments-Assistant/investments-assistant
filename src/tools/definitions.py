"""Claude tool definitions (JSON schemas) for all agent tools."""

TOOL_DEFINITIONS = [
    # ── Market Data ────────────────────────────────────────────────────────────
    {
        "name": "get_stock_data",
        "description": (
            "Fetch OHLCV price data for one or more stocks or ETFs from Yahoo Finance. "
            "Returns open, high, low, close, volume for each candle."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ticker symbols, e.g. ['AAPL', 'SPY', 'QQQ']",
                },
                "period": {
                    "type": "string",
                    "description": "Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd, max",
                    "default": "1mo",
                },
                "interval": {
                    "type": "string",
                    "description": "Candle interval: 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo",
                    "default": "1d",
                },
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "get_crypto_data",
        "description": (
            "Fetch OHLCV price data for one or more cryptocurrencies from Yahoo Finance. "
            "Use symbols like BTC-USD, ETH-USD, SOL-USD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Crypto ticker symbols, e.g. ['BTC-USD', 'ETH-USD']",
                },
                "period": {
                    "type": "string",
                    "description": "Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y",
                    "default": "1mo",
                },
                "interval": {
                    "type": "string",
                    "description": "Candle interval: 1h, 1d, 1wk",
                    "default": "1d",
                },
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "get_market_overview",
        "description": (
            "Get a snapshot of major market indices, VIX (fear index), "
            "treasury yields, and commodity prices."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_technical_indicators",
        "description": (
            "Calculate technical analysis indicators for a symbol. "
            "Returns RSI, MACD, Bollinger Bands, EMA(20/50/200), ATR, OBV."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Ticker symbol, e.g. 'AAPL' or 'BTC-USD'",
                },
                "period": {
                    "type": "string",
                    "description": "Lookback period for the calculation: 3mo, 6mo, 1y",
                    "default": "6mo",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_options_chain",
        "description": (
            "Fetch the options chain for a stock symbol (calls and puts). "
            "Returns strikes, expiries, bid/ask, implied volatility, open interest, delta, gamma."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Underlying stock ticker, e.g. 'AAPL'",
                },
                "expiry": {
                    "type": "string",
                    "description": "Expiry date in YYYY-MM-DD format. If omitted, \
                        returns next 3 expiries.",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "search_ticker",
        "description": "Search for a ticker symbol by company name or keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Company name or keyword, e.g. 'Apple' or 'semiconductor ETF'",
                },
            },
            "required": ["query"],
        },
    },
    # ── News & Sentiment ───────────────────────────────────────────────────────
    {
        "name": "search_market_news",
        "description": (
            "Fetch recent financial news articles for a topic or symbol and analyse sentiment. "
            "Returns article titles, summaries, sources, publication dates, and sentiment scores."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'Apple earnings', 'Bitcoin ETF', \
                        'Fed rate decision'",
                },
                "max_articles": {
                    "type": "integer",
                    "description": "Maximum number of articles to return (1–20)",
                    "default": 10,
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of news sources to filter by, \
                        e.g. ['reuters', 'bloomberg']",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_earnings_calendar",
        "description": "Get upcoming earnings announcements for the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to look (1–30)",
                    "default": 7,
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: filter by specific symbols. If empty, return all.",
                },
            },
            "required": [],
        },
    },
    # ── Portfolio ──────────────────────────────────────────────────────────────
    {
        "name": "get_portfolio_summary",
        "description": (
            "Get the current portfolio summary across all connected brokers: "
            "positions, quantities, average cost, current value, unrealised P&L."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "broker": {
                    "type": "string",
                    "description": "Filter by broker: alpaca, ibkr, coinbase, binance. If omitted, \
                        returns all.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_account_info",
        "description": "Get account balance, buying power, and cash available for a broker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "broker": {
                    "type": "string",
                    "enum": ["alpaca", "ibkr", "coinbase", "binance"],
                    "description": "Which broker account to query",
                },
            },
            "required": ["broker"],
        },
    },
    {
        "name": "get_trade_history",
        "description": "Retrieve recent trade history from a broker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "broker": {
                    "type": "string",
                    "enum": ["alpaca", "ibkr", "coinbase", "binance"],
                },
                "days": {
                    "type": "integer",
                    "description": "How many days back to fetch",
                    "default": 30,
                },
            },
            "required": ["broker"],
        },
    },
    # ── Trade Execution ────────────────────────────────────────────────────────
    {
        "name": "execute_trade",
        "description": (
            "Execute a buy or sell order via a brokerage. "
            "In RECOMMEND mode this creates a pending recommendation requiring user confirmation. "
            "In AUTO mode this submits the order directly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "broker": {
                    "type": "string",
                    "enum": ["alpaca", "ibkr", "coinbase", "binance"],
                    "description": "Which broker to route the order through",
                },
                "symbol": {
                    "type": "string",
                    "description": "Ticker or trading pair, e.g. 'AAPL', 'BTC-USD', 'BTCUSDT'",
                },
                "side": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                },
                "quantity": {
                    "type": "number",
                    "description": "Number of shares / coins. For fractional shares use decimals.",
                },
                "order_type": {
                    "type": "string",
                    "enum": ["market", "limit", "stop_limit"],
                    "default": "market",
                },
                "limit_price": {
                    "type": "number",
                    "description": "Limit price (required for limit / stop_limit orders)",
                },
                "stop_price": {
                    "type": "number",
                    "description": "Stop trigger price (required for stop_limit orders)",
                },
                "reason": {
                    "type": "string",
                    "description": "Mandatory: explain WHY this trade is being placed",
                },
            },
            "required": ["broker", "symbol", "side", "quantity", "reason"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an open order at a broker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "broker": {
                    "type": "string",
                    "enum": ["alpaca", "ibkr", "coinbase", "binance"],
                },
                "order_id": {
                    "type": "string",
                    "description": "The broker order ID to cancel",
                },
            },
            "required": ["broker", "order_id"],
        },
    },
    # ── Simulation ─────────────────────────────────────────────────────────────
    {
        "name": "run_simulation",
        "description": (
            "Run a backtested investment simulation using historical data. "
            "Returns equity curve, total return, Sharpe ratio, max drawdown, and trade list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A descriptive name for this simulation",
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Symbols to include in the simulation",
                },
                "strategy": {
                    "type": "object",
                    "description": (
                        "Strategy parameters. Supported types: "
                        "'buy_and_hold', 'sma_crossover' (params: fast, slow), "
                        "'rsi_mean_reversion' (params: rsi_buy, rsi_sell), "
                        "'momentum' (params: lookback_days)"
                    ),
                    "properties": {
                        "type": {"type": "string"},
                        "params": {"type": "object"},
                    },
                    "required": ["type"],
                },
                "initial_capital": {
                    "type": "number",
                    "description": "Starting capital in USD",
                    "default": 10000,
                },
                "period_start": {
                    "type": "string",
                    "description": "Start date YYYY-MM-DD",
                },
                "period_end": {
                    "type": "string",
                    "description": "End date YYYY-MM-DD (defaults to today)",
                },
            },
            "required": ["name", "symbols", "strategy", "period_start"],
        },
    },
    # ── Agent Control ──────────────────────────────────────────────────────────
    {
        "name": "set_trading_mode",
        "description": "Switch the agent between recommend and auto trading modes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["recommend", "auto"],
                    "description": "'recommend' = agent proposes, user confirms; \
                        'auto' = agent executes automatically",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "generate_report",
        "description": (
            "Generate a comprehensive investment report for a given time period. "
            "Returns a structured HTML report and saves a PDF."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period_start": {
                    "type": "string",
                    "description": "Start date YYYY-MM-DD",
                },
                "period_end": {
                    "type": "string",
                    "description": "End date YYYY-MM-DD (defaults to today)",
                },
            },
            "required": ["period_start"],
        },
    },
]


def to_openai_tools(definitions: list[dict]) -> list[dict]:
    """Convert tool definitions from Claude input_schema format to OpenAI function calling format.

    Claude:  {"name": ..., "description": ..., "input_schema": {...}}
    OpenAI:  {"type": "function", "function": {"name": ..., "description": ..., \
        "parameters": {...}}}
    """
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in definitions
    ]
