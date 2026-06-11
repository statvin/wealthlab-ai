# WealthLab AI — Core (motor quantitativo)

Plataforma de wealth management com simulação estocástica multiativos, adaptada à
realidade brasileira (B3, renda fixa nacional, tributação local). Este repositório
contém, por enquanto, o **núcleo quantitativo** (`wealthlab_core/`): um pacote
Python puro, testável sem rede e sem UI.

> **Aviso.** A ferramenta projeta o futuro **sob hipóteses** — ela não prevê o
> futuro. Os resultados são cenários condicionados às premissas abaixo, não
> garantias. Nada aqui é recomendação de investimento ou orientação fiscal.

## Status

| Fase | Entrega | Status |
|------|---------|--------|
| **1** | Domínio + market data com cache + motor t-Student + renda fixa + fluxos/inflação/rebalanceamento | ✅ concluída |
| 2 | VaR/CVaR, ruína, meta, drawdown, contribuição ao risco | ⏳ |
| 3 | Stress por parâmetros chocados | ⏳ |
| 4 | API FastAPI + SQLite + migrations | ⏳ |
| 5 | Dashboard React/TS | ⏳ |
| 6 | Insights + rebalanceamento (+ aposentadoria) | ⏳ |

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"        # núcleo + ferramentas de teste
# pip install -e ".[market]"   # opcional: yfinance (dados reais). O núcleo não precisa.
```

## Uso rápido

```powershell
python examples/demo_fase1.py
pytest -q
```

Veja `examples/demo_fase1.py` para um exemplo completo (estimação de parâmetros a
partir de dados sintéticos → simulação → percentis do patrimônio).

---

## Metodologia (premissas — leia)

Estas premissas **não são opcionais**: são o contrato do motor.

### Renda variável (ações, ETFs, cripto)
- Processo estocástico **multivariado** com retornos **t-Student** (caudas gordas),
  correlações preservadas via **decomposição de Cholesky**.
- O parâmetro `df` (graus de liberdade) controla a cauda. `df → ∞` recupera o
  caso **lognormal/Browniano clássico**.
- A covariância simulada é **reescalada** por `(df−2)/df` para casar exatamente a
  volatilidade estimada, independentemente de `df` (ver `engine/returns.py`).
- **Cripto** entra no mesmo motor multivariado; no v1 usa o **mesmo `df`** dos
  demais. ⚠️ Por isso o **risco de cauda de cripto tende a ser subestimado** — uma
  cópula com marginais por classe fica como trabalho futuro documentado.

### Renda fixa (classe separada, **não-Browniana**)
- **Não** usa GBM e **não** vem do Yahoo.
- **Pós-fixado (Selic/CDI):** carrego quase-determinístico a partir de uma Selic
  projetada.
- **IPCA+:** carrego real + inflação; risco de marcação a mercado via **duration**
  (`ΔP/P ≈ −duration·Δy`), relevante no stress (Fase 3).

### Correlação
- Estimada do histórico e **estática** na simulação base. A ferramenta sinaliza
  que **correlações sobem em crises** — isso será tratado no módulo de stress
  (correlações → 1).

### Fluxos, inflação e rebalanceamento
- Aportes/saques mensais em todas as trajetórias (evolução recursiva).
- Inflação **fixa** definida pelo usuário; o motor expõe patrimônio **nominal e
  real**.
- Rebalanceamento padrão: **anual ao alvo** (a cada 12 passos, realoca aos pesos
  por classe). Buy-and-hold é opção secundária (`rebalanceamento = NENHUM`).

### Tributação (deferida)
- A tributação brasileira é por ativo, com isenções e tabela regressiva, e passou
  por mudança regulatória recente. No v1 **não cravamos alíquotas**: a arquitetura
  já suporta alíquota por classe, mas os números serão calibrados depois. Não
  substitui orientação fiscal.

---

## Arquitetura (Fase 1)

```
wealthlab_core/
├── domain/        # modelo Pydantic (ativos, carteira, planos, config) + validações
├── marketdata/    # MarketDataProvider (interface) + Synthetic + Yahoo + cache SQLite
├── engine/        # estimação, geração de retornos t-Student, renda fixa, simulador
└── utils/         # logging
```

### As duas camadas de vetorização (o ponto sutil)
1. **Geração de retornos — totalmente vetorizada, sem loop sobre cenários.** A
   matriz de choques correlacionados (`n_cenarios × n_passos × n_ativos`) é gerada
   de uma vez (`engine/returns.py`).
2. **Evolução do patrimônio — loop sobre os ~360 passos de tempo, vetorizado sobre
   os cenários** (`engine/simulator.py`). É inevitável: o patrimônio é recursivo e
   os fluxos são aditivos (`W_t = (W_{t-1} + aporte − saque)·(1 + retorno)`), o que
   não cabe num `cumprod`.

**Performance:** 10.000 cenários × 30 anos × passo mensal × 5 ativos em ~1 segundo.

## Testes

`pytest -q` — 38 testes cobrindo: validações de domínio, recuperação de μ/σ/corr de
dados sintéticos, propriedades da t-Student (covariância-alvo, gordura de cauda),
carrego de renda fixa, fluxos/saques/ruína, rebalanceamento, reprodutibilidade por
seed e o critério de performance.
