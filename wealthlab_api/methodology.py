"""Texto da aba Metodologia (exposto em GET /methodology).

Requisito da spec: o produto deve expor as premissas. Mantemos a fonte única
aqui, estruturada para o frontend consumir.
"""

from __future__ import annotations

METHODOLOGY = {
    "aviso": (
        "A ferramenta projeta o futuro SOB HIPÓTESES — não prevê o futuro. Os "
        "resultados são cenários condicionados às premissas abaixo, não garantias. "
        "Nada aqui é recomendação de investimento ou orientação fiscal."
    ),
    "premissas": {
        "renda_variavel": (
            "Processo estocástico multivariado com retornos t-Student (caudas "
            "gordas), correlações preservadas via decomposição de Cholesky. O "
            "parâmetro df controla a cauda; df→∞ recupera o caso lognormal/"
            "Browniano. A covariância simulada é reescalada por (df-2)/df para "
            "casar a volatilidade estimada independentemente de df."
        ),
        "cripto": (
            "Entra no mesmo motor multivariado, no v1 com o MESMO df dos demais. "
            "Por isso o risco de cauda de cripto tende a ser SUBESTIMADO — uma "
            "cópula com marginais por classe fica como trabalho futuro."
        ),
        "renda_fixa": (
            "Classe separada, não-Browniana e não vinda do Yahoo. Pós-fixado "
            "(Selic/CDI): carrego quase-determinístico. IPCA+: carrego real + "
            "inflação, com marcação a mercado via duration (ΔP/P ≈ −duration·Δy) "
            "relevante no stress."
        ),
        "correlacao": (
            "Estimada do histórico e estática na simulação base. Em crises as "
            "correlações sobem — tratado no stress (correlações → 1)."
        ),
        "tributacao": (
            "Deferida. A arquitetura suporta alíquota por classe, mas os números "
            "serão calibrados depois. Não substitui orientação fiscal."
        ),
        "inflacao": (
            "Taxa fixa definida pelo usuário; o motor expõe patrimônio nominal e "
            "real."
        ),
    },
    "metricas": {
        "var_cvar": (
            "VaR e CVaR (95% e 99%) sobre a distribuição do retorno da carteira em "
            "1 ano (pesos atuais, buy-and-hold, sem fluxos) — risco de mercado. "
            "CVaR = Expected Shortfall (perda média na cauda)."
        ),
        "prob_ruina": (
            "Fração de trajetórias que tocam zero em qualquer ponto até o "
            "horizonte total. Distinta do VaR."
        ),
        "prob_meta": "Fração de trajetórias com patrimônio ≥ meta no prazo.",
        "drawdown": "Maior queda pico-a-vale por trajetória (médio, mediano, pior).",
        "contribuicao_risco": (
            "Decomposição da variância da carteira por ativo/classe (marginal "
            "contribution to risk)."
        ),
    },
    "stress": (
        "Choques estilizados por parâmetros (drift↓, vol↑, correlações→1, choque "
        "de juros no IPCA+ via duration), NÃO replays históricos exatos. Presets: "
        "2008, COVID-2020, Estagflação, Brasil-2015."
    ),
}
