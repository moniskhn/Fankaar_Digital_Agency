"""
Fankaar Digital — Configuration Management
Uses pydantic-settings for environment-based configuration.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── LLM Configuration ──────────────────────────────────────────
    llm_provider: str = Field(default="ollama", description="LLM provider: ollama, anthropic, or openai")
    ollama_host: str = Field(default="host.docker.internal:11434", description="Ollama server host:port")
    ollama_model: str = Field(default="llama3.2", description="Default Ollama model name")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic model name")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    llm_temperature: float = Field(default=0.7, description="LLM sampling temperature")
    llm_max_tokens: int = Field(default=4096, description="Max tokens per LLM response")
    llm_timeout: int = Field(default=120, description="LLM request timeout in seconds")

    # ── WhatsApp / Twilio ──────────────────────────────────────────
    twilio_account_sid: str = Field(default="", description="Twilio Account SID")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
    twilio_whatsapp_number: str = Field(default="", description="Twilio WhatsApp sender number")
    owner_whatsapp_number: str = Field(default="", description="Owner's WhatsApp number")
    owner_name: str = Field(default="Boss", description="Owner's preferred name")

    # ── Agency Settings ────────────────────────────────────────────
    agency_name: str = Field(default="Fankaar Digital", description="Agency name")
    daily_report_time: str = Field(default="09:00", description="Daily report time HH:MM")
    daily_report_timezone: str = Field(default="Asia/Dubai", description="Daily report timezone")
    max_concurrent_campaigns: int = Field(default=10, description="Max concurrent campaigns")
    default_campaign_phases: List[str] = Field(
        default=["brief", "strategy", "creation", "review", "approval", "live", "reporting", "completed"],
        description="Campaign lifecycle phases"
    )

    # ── Database ───────────────────────────────────────────────────
    database_path: str = Field(default="/app/data/fankaar.db", description="SQLite database path")

    # ── Stripe Billing ─────────────────────────────────────────────
    stripe_secret_key: str = Field(default="", description="Stripe secret API key (sk_test_... or sk_live_...)")
    stripe_publishable_key: str = Field(default="", description="Stripe publishable key (pk_test_... or pk_live_...)")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook endpoint secret (whsec_...)")
    stripe_starter_price_id: str = Field(default="", description="Stripe Price ID for Starter monthly plan")
    stripe_starter_annual_price_id: str = Field(default="", description="Stripe Price ID for Starter annual plan")
    stripe_growth_price_id: str = Field(default="", description="Stripe Price ID for Growth monthly plan")
    stripe_growth_annual_price_id: str = Field(default="", description="Stripe Price ID for Growth annual plan")
    stripe_enterprise_price_id: str = Field(default="", description="Stripe Price ID for Enterprise monthly plan")
    stripe_enterprise_annual_price_id: str = Field(default="", description="Stripe Price ID for Enterprise annual plan")

    @property
    def has_stripe_configured(self) -> bool:
        """Check if Stripe credentials are configured."""
        return bool(self.stripe_secret_key)

    # ── Regional Intelligence ──────────────────────────────────────
    regional_cache_ttl_hours: int = Field(default=168, description="Regional profile cache TTL")
    web_search_timeout: int = Field(default=30, description="Web search timeout in seconds")

    # ── Application ────────────────────────────────────────────────
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"], description="Allowed CORS origins")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """SQLAlchemy database URL."""
        return f"sqlite:///{self.database_path}"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def has_twilio_configured(self) -> bool:
        """Check if Twilio credentials are configured."""
        return all([
            self.twilio_account_sid,
            self.twilio_auth_token,
            self.twilio_whatsapp_number,
            self.owner_whatsapp_number
        ])

    @property
    def llm_fallback_chain(self) -> List[str]:
        """LLM provider fallback chain."""
        providers = [self.llm_provider]
        all_providers = ["anthropic", "openai", "ollama"]
        for p in all_providers:
            if p not in providers:
                providers.append(p)
        return providers


# Global settings instance
settings = Settings()
