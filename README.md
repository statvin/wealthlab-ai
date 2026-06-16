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
| **2** | VaR/CVaR, ruína, meta, drawdown, contribuição ao risco | ✅ concluída |
| **3** | Stress por parâmetros chocados | ✅ concluída |
| **4** | API FastAPI + SQLite + migrations | ✅ concluída |
| **5** | Dashboard React/TS | ✅ concluída |
| **6** | Insights + rebalanceamento + aposentadoria | ✅ concluída |

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
partir de dados sintéticos → simulação → percentis do patrimônio). Há também
`demo_fase2.py` (risco) e `demo_fase3.py` (stress, Base vs. Stress).

## API (Fase 4)

Casca fina FastAPI sobre o motor. Instale o extra e rode as migrations antes de
subir o servidor:

```powershell
pip install -e ".[api]"
alembic upgrade head                 # cria o schema no SQLite
uvicorn wealthlab_api.main:app --reload
# Swagger interativo em http://127.0.0.1:8000/docs
```

Endpoints:

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/portfolio` | cria carteira (valida pelas regras do domínio) |
| GET | `/portfolio/{id}` | consulta carteira |
| POST | `/simulation/run` | roda a simulação (síncrono) e persiste com a seed |
| GET | `/simulation/{id}/results` | resumo + funil (amostra + bandas P5..P95) |
| GET | `/simulation/{id}/risk-analysis` | VaR/CVaR, ruína, meta, drawdown, contribuição |
| GET | `/simulation/{id}/stress-test` | Base vs. Stress (query `presets=2008,COVID-2020`) |
| GET | `/simulation/{id}/insights` | insights por regras (cada um rastreável a uma métrica) |
| POST | `/simulation/{id}/rebalance` | compras/vendas vs. alvo desejado (body: alvo por classe) |
| POST | `/simulation/{id}/retirement` | "posso me aposentar?": prob. de sucesso e saque sustentável |
| GET | `/methodology` | premissas da aba Metodologia |

A simulação grava `seed` + entradas, então a mesma requisição é **reproduzível**.
Persistência: inputs + seed + métricas resumidas + ~100 trajetórias e bandas (o
suficiente para o funil da Fase 5), sem guardar o array bruto completo.
`/simulation/{id}/rebalance` fica para a Fase 6 (depende do motor de recomendação).

## Frontend (Fase 5)

Dashboard React + TypeScript + Vite + TailwindCSS + Plotly.js (tema escuro). Cliente
da API tipado à mão; estado via hooks próprios (sem libs externas). Gráficos: funil
de Monte Carlo (100 trajetórias + bandas P5..P95), heatmap de correlação, histograma
dos patrimônios finais, KPIs com tooltips e aba Metodologia.

Para a demo rodar **offline** (sem depender do Yahoo), popule o cache de preços:

```powershell
# 1) Backend (a partir da raiz do projeto)
pip install -e ".[api]"
alembic upgrade head
python scripts/seed_cache.py          # cache sintético dos tickers da carteira-modelo
uvicorn wealthlab_api.main:app --port 8000

# 2) Frontend (em frontend/)
npm install
npm run dev                           # http://localhost:5173 (proxy /api -> :8000)
```

`npm run build` (typecheck + bundle) e `npm test` (Vitest + Testing Library) validam o
front. O dev server faz proxy de `/api` para o FastAPI, então não há CORS no dev.

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

`pytest -q` — 86 testes do motor + API cobrindo: validações de domínio, recuperação
de μ/σ/corr de dados sintéticos, propriedades da t-Student (covariância-alvo, gordura
de cauda), carrego de renda fixa, fluxos/saques/ruína, rebalanceamento, métricas de
risco, stress, integração da API e reprodutibilidade por seed. No front, `npm test`
roda 9 testes de componentes (Vitest + Testing Library).

## Licença

**© 2026 Vinícius Ramos. Todos os direitos reservados.** Este repositório é público
apenas para fins de portfólio e avaliação. Ver o código **não** concede direito de
uso — nenhuma permissão de usar, copiar, modificar ou redistribuir é dada sem
autorização escrita. Ver [LICENSE](LICENSE).
