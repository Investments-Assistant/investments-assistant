# Investment Assistant

A private, home-hosted investment assistant that runs entirely on a **Raspberry Pi 5**.
It monitors stock, ETF, crypto, and options markets in real time, executes or recommends
trades through four broker integrations, and is accessible from anywhere in the world
through a private WireGuard VPN — with no data leaving your network.

LLM inference is **fully local**: models are loaded directly into process memory via
`llama-cpp-python` (GGUF) or HuggingFace `transformers`. No external AI API is used.

---

## Features

- **18 agent tools** — market data, technical indicators, options chains, news sentiment,
  portfolio management, trade execution, backtesting, report generation
- **4 broker integrations** — Alpaca (stocks/ETFs), Interactive Brokers (stocks/options),
  Coinbase (crypto), Binance (crypto)
- **Two trading modes** — `recommend` (agent proposes, you confirm) or `auto` (agent
  executes within configurable safety limits)
- **Real-time streaming chat** — FastAPI + WebSocket; token-by-token response
- **Scheduled autonomous scans** — market data refreshed every 5 min; optional autonomous
  market scanning in auto mode
- **Weekly reports** — HTML + PDF with full reasoning transparency
- **Pi-hole** — network-wide DNS ad blocker for every device on your LAN
- **WireGuard VPN** — private, cryptographically authenticated remote access from anywhere
- **No cloud dependency** — the LLM runs on-device; your data stays home

---

## Architecture

```
Browser / Phone
     │  (WireGuard VPN — only authenticated devices)
     ▼
  Nginx  ──  IP whitelist + rate limiting
     │
     ▼
  FastAPI  ──  WebSocket chat  ──  InvestmentOrchestrator
                                          │
                            ┌─────────────┴──────────────┐
                            ▼                            ▼
                     LLM Backend                   Tool Dispatcher
                  (llama_cpp / hf)            (18 tools → brokers,
                                              market data, news, etc.)
     ▼              ▼               ▼
PostgreSQL         Redis        APScheduler
(chat history,   (cache)      (market refresh,
 trades, reports)              weekly reports,
                               autonomous scans)
```

---

## Project Structure

```
investments-assistant/
├── Dockerfile                        # ARM64-optimised, compiles llama-cpp-python
├── docker-compose.yml                # app, postgres, redis, pihole, nginx
├── Makefile                          # common commands
├── pyproject.toml                    # Poetry dependencies
├── .env.example                      # environment template
│
├── config/
│   ├── nginx/
│   │   ├── investment-assistant.conf # IP whitelist, HTTPS, WebSocket proxy
│   │   └── rate-limit.conf           # Nginx rate-limiting zones
│   ├── wireguard/
│   │   ├── wg0.conf.template         # server config (fill in keys)
│   │   ├── client.conf.template      # per-device client config
│   │   └── setup.md                  # WireGuard setup guide
│   └── pihole/
│       └── setup.md                  # Pi-hole setup guide
│
├── models/                           # GGUF model files go here (bind-mounted)
│
├── scripts/
│   ├── setup.sh                      # automated Pi 5 setup (Docker, WireGuard, firewall)
│   └── download_model.py             # download GGUF models from HuggingFace
│
└── src/
    ├── app.py                        # FastAPI application entry point
    ├── config.py                     # pydantic-settings configuration
    │
    ├── agent/
    │   ├── clients/
    │   │   ├── base.py               # BaseLLMClient ABC
    │   │   ├── llama_cpp_client.py   # GGUF inference (recommended for Pi 5)
    │   │   └── transformers_client.py# HuggingFace inference (GPU preferred)
    │   ├── orchestrator.py           # stateful per-session agent loop
    │   └── prompts.py                # system prompt + weekly report prompt
    │
    ├── tools/
    │   ├── definitions.py            # 18 tool schemas + OpenAI format converter
    │   ├── dispatcher.py             # routes tool calls to implementations
    │   ├── market_data.py            # yfinance: OHLCV, indicators, options, earnings
    │   ├── news.py                   # RSS + NewsAPI with sentiment analysis
    │   ├── portfolio.py              # cross-broker portfolio aggregation
    │   ├── alpaca.py                 # Alpaca Markets integration
    │   ├── ibkr.py                   # Interactive Brokers integration
    │   ├── coinbase.py               # Coinbase Advanced Trade integration
    │   ├── binance_tool.py           # Binance integration
    │   └── simulator.py             # backtesting engine
    │
    ├── db/
    │   ├── database.py               # SQLAlchemy async engine
    │   └── models.py                 # ChatMessage, Trade, Analysis, Report, etc.
    │
    ├── scheduler/
    │   ├── jobs.py                   # APScheduler jobs
    │   └── reporter.py               # weekly HTML+PDF report generator
    │
    └── web/
        ├── routes.py                 # HTTP + WebSocket endpoints
        └── static/                   # index.html, app.js, style.css
```

---

## LLM Backends

Two backends are available. Neither makes external API calls.

### `llama_cpp` (recommended for Pi 5)

Uses `llama-cpp-python` to load **GGUF quantised models** directly into memory.
ARM NEON-optimised; designed for CPU inference.

```bash
# Download a model
python scripts/download_model.py --list
python scripts/download_model.py qwen2.5-7b --output-dir ./models

# .env
LLM_BACKEND=llama_cpp
LLM_MODEL_PATH=/app/models/qwen2.5-7b-instruct-q4_k_m.gguf
```

Tested models on Pi 5 (8 GB RAM):

| Model | Size | Notes |
| --- | --- | --- |
| `qwen2.5-7b` | ~4.7 GB | Best quality/speed — recommended |
| `llama3.2-3b` | ~3.4 GB | Faster, lower RAM |
| `mistral-7b` | ~4.4 GB | Solid all-rounder |
| `llama3.1-8b` | ~4.9 GB | Strong tool use |

### `transformers` (GPU preferred)

Uses HuggingFace `transformers` + `torch` to load **safetensors models**.
Slower on CPU; better on CUDA/MPS.

```bash
# .env
LLM_BACKEND=transformers
LLM_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
LLM_DEVICE=cpu   # or cuda
```

---

## Security Model

The app is **not publicly reachable**. The only port forwarded on your router is
**UDP 51820** (WireGuard). Everything else is blocked at four layers:

1. **WireGuard** — silently drops all packets from unknown peers (no response to attackers)
2. **DOCKER-USER iptables** — kernel-level drop of 80/443 from non-VPN IPs, even if Docker binds to `0.0.0.0`
3. **Nginx IP whitelist** — application-layer check; rate limiting (60 req/min)
4. **FastAPI `is_ip_allowed()`** — belt-and-suspenders in-process check

Authentication = your WireGuard private key. No passwords. No exposed login page.
See [config/wireguard/setup.md](config/wireguard/setup.md) for full setup instructions.

---

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for the full step-by-step deployment guide.

```bash
# 1. Run the automated Pi setup (Docker, WireGuard, certs, firewall)
bash scripts/setup.sh

# 2. Download a model
python scripts/download_model.py qwen2.5-7b --output-dir ./models

# 3. Configure .env
cp .env.example .env && nano .env

# 4. Start everything
make docker-up

# 5. Access via WireGuard VPN
# https://10.8.0.1
```

---

## Configuration

All settings are read from `.env`. Copy `.env.example` as a starting point.

Key groups:

| Group | Variables |
| --- | --- |
| LLM | `LLM_BACKEND`, `LLM_MODEL_PATH` / `LLM_MODEL_NAME`, `AGENT_MAX_TOKENS` |
| Trading | `TRADING_MODE`, `AUTO_MAX_TRADE_USD`, `AUTO_DAILY_LOSS_LIMIT_USD` |
| Security | `ALLOWED_IPS` |
| Database | `POSTGRES_PASSWORD` |
| Brokers | `ALPACA_API_KEY`, `COINBASE_API_KEY`, `BINANCE_API_KEY`, `IBKR_ENABLED` |
| News | `NEWSAPI_KEY` |
| Pi-hole | `PIHOLE_PASSWORD`, `TZ` |

---

## Development

```bash
make install       # install dependencies (Poetry)
make dev           # run with hot reload
make lint          # ruff check
make format        # ruff format
make test          # pytest
```

---

## Disclaimer

This assistant provides investment analysis and execution assistance for informational
purposes only. It does not constitute financial advice. Past performance does not
guarantee future results. Always consult a qualified financial advisor before making
investment decisions.
