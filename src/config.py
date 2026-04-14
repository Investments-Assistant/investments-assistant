"""Central application configuration via pydantic-settings (reads from .env)."""

from __future__ import annotations

from functools import lru_cache
import ipaddress
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    environment: Literal["development", "production"] = "production"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── Security ───────────────────────────────────────────────────────────────
    allowed_ips: str = "10.8.0.0/24"  # comma-separated CIDRs / IPs

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_networks(self) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        networks = []
        for entry in self.allowed_ips.split(","):
            entry = entry.strip()
            if not entry:
                continue
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                pass
        return networks

    def is_ip_allowed(self, ip: str) -> bool:
        """Return True if *ip* matches any configured CIDR / host entry."""
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(addr in net for net in self.allowed_networks)

    # ── LLM backend (local, in-process — no external APIs) ────────────────────
    # llama_cpp      GGUF models via llama-cpp-python  (recommended for Pi 5)
    # transformers   HuggingFace safetensors models via transformers + torch
    llm_backend: str = "llama_cpp"

    # --- llama_cpp settings ---------------------------------------------------
    # Absolute path to the GGUF model file on disk.
    llm_model_path: str = "/app/models/qwen2.5-7b-instruct-q4_k_m.gguf"
    # Context window in tokens (reduce if you run out of RAM).
    llm_context_size: int = 4096
    # GPU layers to offload: 0 = CPU only (Pi 5 has no GPU), -1 = all to GPU.
    llm_n_gpu_layers: int = 0

    # --- transformers settings ------------------------------------------------
    # HuggingFace model ID (auto-downloads on first run) or local directory path.
    llm_model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    # Inference device: cpu | cuda | mps
    llm_device: str = "cpu"

    # --- shared ---------------------------------------------------------------
    agent_max_tokens: int = 2048
    agent_temperature: float = 0.1

    # ── Trading ────────────────────────────────────────────────────────────────
    trading_mode: Literal["recommend", "auto"] = "recommend"
    auto_max_trade_usd: float = 500.0
    auto_daily_loss_limit_usd: float = 1000.0
    auto_allowed_symbols: str = ""  # empty = all allowed

    @computed_field  # type: ignore[prop-decorator]
    @property
    def auto_allowed_symbols_set(self) -> set[str]:
        if not self.auto_allowed_symbols.strip():
            return set()
        return {s.strip().upper() for s in self.auto_allowed_symbols.split(",")}

    # ── Database ───────────────────────────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "investment_assistant"
    postgres_user: str = "ia_user"
    postgres_password: str = "change_me"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ──────────────────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── Alpaca ─────────────────────────────────────────────────────────────────
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_paper: bool = True

    # ── Interactive Brokers ────────────────────────────────────────────────────
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 4002
    ibkr_client_id: int = 1
    ibkr_enabled: bool = False

    # ── Coinbase ───────────────────────────────────────────────────────────────
    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""

    # ── Binance ────────────────────────────────────────────────────────────────
    binance_api_key: str = ""
    binance_secret_key: str = ""
    binance_testnet: bool = True

    # ── News ───────────────────────────────────────────────────────────────────
    newsapi_key: str = ""

    # ── Scheduler ─────────────────────────────────────────────────────────────
    market_data_refresh_minutes: int = 5
    weekly_report_day: int = 6  # 0=Monday, 6=Sunday
    weekly_report_hour: int = 18
    weekly_report_minute: int = 0

    # ── Reports ────────────────────────────────────────────────────────────────
    reports_dir: str = "/app/reports"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience singleton
settings = get_settings()
