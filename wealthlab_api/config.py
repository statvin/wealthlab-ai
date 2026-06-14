"""Configuração da API via variáveis de ambiente (.env)."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings da API. Prefixo de env: WEALTHLAB_ (ex.: WEALTHLAB_DB_URL)."""

    model_config = SettingsConfigDict(
        env_prefix="WEALTHLAB_", env_file=".env", extra="ignore"
    )

    db_url: str = "sqlite:///./data/wealthlab.sqlite"
    cache_path: str = "data/cache/market.sqlite"
    log_level: str = "INFO"
    # Janela de histórico usada para estimar μ/σ/correlação da renda variável.
    historico_anos: int = 10


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Garante a pasta do SQLite (db_url no formato sqlite:///caminho).
    if settings.db_url.startswith("sqlite:///"):
        caminho = settings.db_url.removeprefix("sqlite:///")
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
    return settings
