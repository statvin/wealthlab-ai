"""Logging estruturado e centralizado do pacote.

Mantemos um único ponto de configuração para que domínio, market data e motor
compartilhem o mesmo formato. Em fases futuras (API) isto facilita plugar um
handler JSON sem mexer no resto do código.
"""

from __future__ import annotations

import logging
import os

_CONFIGURADO = False


def get_logger(nome: str) -> logging.Logger:
    """Devolve um logger nomeado, configurando o root do pacote uma única vez.

    O nível vem da env `WEALTHLAB_LOG_LEVEL` (default INFO). Usamos `nome` no
    padrão `wealthlab_core.<modulo>` para que o filtro por namespace funcione.
    """
    global _CONFIGURADO
    if not _CONFIGURADO:
        nivel = os.getenv("WEALTHLAB_LOG_LEVEL", "INFO").upper()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root = logging.getLogger("wealthlab_core")
        root.setLevel(getattr(logging, nivel, logging.INFO))
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURADO = True

    return logging.getLogger(nome)
