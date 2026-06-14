"""Testes de integração da API (Fase 4).

Tudo offline e determinístico: o banco é um SQLite temporário (tabelas via
metadata) e o market data é um provedor sintético com seed fixa, sobrescrito por
injeção de dependência.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from wealthlab_core.marketdata import MarketDataProvider
from wealthlab_core.marketdata.synthetic import SyntheticProvider
from wealthlab_api.database import Base, get_db
from wealthlab_api.main import app
from wealthlab_api.market import get_market_provider


# Histórico sintético fixo para AAA/BBB (datas fixas -> determinístico).
_PRECOS = SyntheticProvider(
    tickers=["AAA", "BBB"],
    mu_anual=np.array([0.12, 0.10]),
    sigma_anual=np.array([0.22, 0.18]),
    correlacao=np.array([[1.0, 0.3], [0.3, 1.0]]),
    seed=99,
).get_history(["AAA", "BBB"], date(2004, 1, 1), date(2024, 1, 1))


class _FakeProvider(MarketDataProvider):
    """Ignora as datas pedidas e devolve o histórico fixo (determinístico)."""

    def get_history(self, tickers, inicio, fim):
        return _PRECOS[list(tickers)]


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_market_provider] = lambda: _FakeProvider()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --------------------------- payloads de apoio ----------------------------
def _carteira_payload():
    return {
        "nome": "Carteira teste",
        "holdings": [
            {
                "asset": {"ticker": "AAA", "nome": "Acao A", "classe": "EQUITY_BR"},
                "quantidade": 100,
                "preco_inicial": 100.0,
            },
            {
                "asset": {"ticker": "BBB", "nome": "Acao B", "classe": "EQUITY_INTL"},
                "quantidade": 100,
                "preco_inicial": 100.0,
            },
            {
                "asset": {
                    "ticker": "CDB",
                    "nome": "CDB 100% CDI",
                    "classe": "FIXED_INCOME_POS",
                    "fixed_income_terms": {"indexador": "CDI", "taxa_contratada": 1.0},
                },
                "quantidade": 20000,
                "preco_inicial": 1.0,
            },
        ],
    }


def _run_payload(portfolio_id):
    return {
        "portfolio_id": portfolio_id,
        "config": {"n_cenarios": 2000, "horizonte_anos": 10.0, "seed": 7},
        "premissas_juros": {"selic_aa": 0.10, "ipca_aa": 0.04},
        "cashflow": {"aporte_mensal": 500.0},
        "target": {
            "por_classe": {"EQUITY_BR": 0.4, "EQUITY_INTL": 0.4, "FIXED_INCOME_POS": 0.2}
        },
        "goal": {"valor_meta": 500000.0, "prazo_anos": 10.0},
    }


def _criar_carteira(client) -> int:
    r = client.post("/portfolio", json=_carteira_payload())
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ------------------------------- testes -----------------------------------
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_methodology(client):
    r = client.get("/methodology")
    assert r.status_code == 200
    body = r.json()
    assert "premissas" in body and "renda_variavel" in body["premissas"]


def test_criar_e_obter_carteira(client):
    pid = _criar_carteira(client)
    r = client.get(f"/portfolio/{pid}")
    assert r.status_code == 200
    assert {h["ticker"] for h in r.json()["holdings"]} == {"AAA", "BBB", "CDB"}


def test_obter_carteira_inexistente_404(client):
    assert client.get("/portfolio/999").status_code == 404


def test_carteira_renda_fixa_sem_termos_422(client):
    payload = {
        "holdings": [
            {
                "asset": {"ticker": "CDB", "nome": "CDB", "classe": "FIXED_INCOME_POS"},
                "quantidade": 1000,
            }
        ]
    }
    r = client.post("/portfolio", json=payload)
    assert r.status_code == 422  # validação de domínio (RF exige termos)


def test_rodar_simulacao_e_resultados(client):
    pid = _criar_carteira(client)
    r = client.post("/simulation/run", json=_run_payload(pid))
    assert r.status_code == 201, r.text
    sim_id = r.json()["id"]
    assert r.json()["resumo"]["nominal"]["p50"] > 0

    res = client.get(f"/simulation/{sim_id}/results")
    assert res.status_code == 200
    funil = res.json()["funil"]
    assert len(funil["meses"]) == 121  # 10 anos * 12 + 1
    assert len(funil["amostra"]) == 100
    assert set(funil["bandas"]) == {"p5", "p10", "p50", "p90", "p95"}


def test_reprodutibilidade_por_seed(client):
    pid = _criar_carteira(client)
    r1 = client.post("/simulation/run", json=_run_payload(pid)).json()
    r2 = client.post("/simulation/run", json=_run_payload(pid)).json()
    # Mesma carteira, mesma seed -> mesmos percentis.
    assert r1["resumo"]["nominal"] == r2["resumo"]["nominal"]


def test_risk_analysis(client):
    pid = _criar_carteira(client)
    sim_id = client.post("/simulation/run", json=_run_payload(pid)).json()["id"]
    r = client.get(f"/simulation/{sim_id}/risk-analysis")
    assert r.status_code == 200
    body = r.json()
    niveis = {vc["nivel"] for vc in body["var_cvar"]}
    assert niveis == {0.95, 0.99}
    assert 0.0 <= body["prob_ruina"] <= 1.0
    assert "FIXED_INCOME_POS" in body["contribuicao"]["por_classe"]


def test_stress_test(client):
    pid = _criar_carteira(client)
    sim_id = client.post("/simulation/run", json=_run_payload(pid)).json()["id"]

    r = client.get(f"/simulation/{sim_id}/stress-test", params={"presets": "2008"})
    assert r.status_code == 200
    comps = r.json()["comparacoes"]
    assert len(comps) == 1 and comps[0]["nome"] == "2008"
    base, stress = comps[0]["resumo"]["p50_final"]
    assert stress < base  # stress é pior

    # preset desconhecido -> 400
    assert client.get(
        f"/simulation/{sim_id}/stress-test", params={"presets": "INEXISTENTE"}
    ).status_code == 400


def test_run_carteira_inexistente_404(client):
    r = client.post("/simulation/run", json=_run_payload(999))
    assert r.status_code == 404
