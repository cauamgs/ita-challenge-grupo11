# Handoff — Motor de decisão (v2)

Este pacote é o protótipo v1 do Grupo 11 **sem o motor de decisão**. A aplicação está pronta:
importa uma rodada de recomendações, mostra a lista e o detalhe ao analista, registra as decisões
(aprovar/editar/rejeitar/adiar), calcula as métricas e exporta as aprovadas. O que falta é a parte
matemática: **gerar a rodada** — para cada SKU × canal, a recomendação, o preço sugerido, o risco, a
prioridade e a justificativa.

O arquivo de resultados da rodada de exemplo (`seed/recomendacoes_rodada_2026-09-09.csv`) foi
**retirado de propósito**: o motor deve produzir esses resultados a partir dos dados de entrada.

## 1. O que você recebe

| Item | Onde |
|---|---|
| Problema, regras de negócio R01–R12, indicadores e o dicionário da saída esperada | `docs/CONTEXTO_DESAFIO.md` |
| Hipótese de solução do grupo (etapas do motor, modelos, como cada requisito é atendido) | `docs/referencia/Grupo11_Semana2_Hipotese_PopularPet.pdf` |
| Diagnóstico do problema | `docs/referencia/Grupo11_Semana1_Diagnostico_PopularPet.pdf` |
| Dados de entrada (fictícios) da empresa | `seed/base_popular_pet.xlsx` |
| Ponto de extensão onde o motor se encaixa | `backend/app/engine/base.py` |
| Telas, fluxo do analista, API e modelo de dados | `docs/ESPECIFICACAO_V1.md`, `docs/API.md`, `docs/DATA_MODEL.md` |

### Dados de entrada (`seed/base_popular_pet.xlsx`)

Cada aba tem 2 linhas de título antes do cabeçalho (`pd.read_excel(..., header=2)`); datas em
`dd/mm/aaaa`; canais "Loja física", "E-commerce", "Marketplace".

| Aba | Linhas | Colunas |
|---|---|---|
| Produtos | 40 | SKU, Produto, Categoria, Marca, Curva ABC, Status, Preço atual, Custo reposição, Margem mínima, Margem alvo, Estoque atual, Cobertura (dias), Venda média/dia |
| Precos_Atuais | 120 | SKU, Canal, Preço atual, Data referência |
| Custos_Margens | 120 | SKU, Canal, Custo reposição, Impostos estimados, Frete rateado, Taxa canal, Margem mínima, Margem alvo, Custo total referência |
| Vendas_12m | 1.440 | Mês, SKU, Canal, Quantidade, Receita, Preço médio, Desconto médio |
| Estoque | 40 | SKU, Estoque atual, Cobertura dias, Pedido compra aberto, Previsão recebimento, Local |
| Concorrencia | 120 | SKU, Concorrente, Correspondência, Preço, Disponível, Frete, Data/hora coleta, Confiabilidade matching |
| Historico_Precos | 120 | SKU, Data, Preço, Motivo, Origem |
| Promocoes | 8 | SKU, Campanha, Início, Fim, Desconto, Regra |
| Regras_Negocio | 12 | ID, Tema, Regra fictícia, Ação esperada, Criticidade |
| Indicadores_Atuais | 8 | Indicador, Valor fictício atual, Meta fictícia, Frequência, Responsável |

O seed já carrega no PostgreSQL as abas **Produtos**, **Precos_Atuais + Custos_Margens** (tabela
`product_channel_state`) e **Estoque** (`stock_snapshot`). As demais (vendas, concorrência,
histórico, promoções) **não estão no banco**: leia direto do xlsx ou crie tabelas novas com
migration Alembic (`backend/alembic/versions/`), seguindo o padrão de `backend/app/seed/base_xlsx.py`.

## 2. O contrato do motor

O motor implementa o protocolo de `backend/app/engine/base.py`:

```python
class RecommendationEngine(Protocol):
    source: str                                   # gravado em rounds.source — use "engine"
    def run(self, round_date: date) -> list[RecommendationIn]: ...
```

`run` devolve **uma `RecommendationIn` por SKU × canal** (120 itens com a base atual). Os campos
espelham as colunas descritas em `docs/CONTEXTO_DESAFIO.md` ("O arquivo de recomendações"):

| Campo (`RecommendationIn`) | Coluna equivalente | Observação |
|---|---|---|
| `priority` | prioridade | 1 = maior valor em jogo; define a ordem padrão da lista |
| `sku`, `product_name`, `category`, `abc_curve`, `channel` | sku, produto, categoria, curva_abc, canal | `channel`: `LOJA_FISICA`, `ECOMMERCE`, `MARKETPLACE` |
| `current_price`, `market_price`, `lowest_valid_competitor`, `cost` | preco_atual, preco_mercado, menor_concorrente, custo | R$ |
| `current_margin`, `min_margin`, `target_margin`, `net_margin` | margem_atual, margem_minima, margem_alvo, margem_liquida | fração 0–1 |
| `stock_qty`, `coverage_days`, `sales_trend_month`, `sales_var_12m` | estoque, cobertura_dias, tendencia_mes, var_12m | tendências em fração (−0,03 = −3%/mês) |
| `recommendation` | recomendacao | `SUBIR`, `BAIXAR`, `MANTER`, `REVISAR` |
| `suggested_price`, `variation`, `resulting_margin` | preco_sugerido, variacao, margem_resultante | `variation` = sugerido/atual − 1; MANTER → sugerido = atual |
| `risk_level`, `risk_score` | nivel_risco, risco_score | `BAIXO`/`MEDIO`/`ALTO`; score 0–100 |
| `data_confidence` | confianca_dados | 0–1 |
| `requires_approval` | exige_aprovacao | curva A com variação > 3%, estratégico, alto risco… |
| `est_monthly_revenue`, `est_monthly_impact` | receita_mensal_est, impacto_mensal_est | R$/mês |
| `justification` | justificativa | texto em português exibido ao analista |
| `review_reasons`, `data_alerts` | motivos_revisao, alertas_dados | listas de textos; cite a regra entre parênteses, ex. "(R09)" — a tela mostra o texto da regra |

O que a interface faz com esses campos (não precisa reimplementar): valor em jogo =
`est_monthly_revenue × |variation|`; piso de margem = `cost / (1 − min_margin)` (aviso R01 ao editar);
resumo da rodada agrupa `review_reasons` por palavra-chave ("campanha", "cobertura",
"dados"/"confiança").

## 3. Como ligar o motor à aplicação

Há dois caminhos; o primeiro é o definitivo.

**a) Implementar o protocolo (recomendado).** Crie, por exemplo, `backend/app/engine/pricing.py`
com uma classe `PricingEngine` (`source = "engine"`) e grave a rodada com o service que já existe:

```python
from datetime import date
from app.db import SessionLocal
from app.engine.pricing import PricingEngine
from app.services.rounds import run_engine

with SessionLocal() as session:
    run_engine(session, PricingEngine(...), date(2026, 9, 9))   # valida SKUs, cria rounds + recommendations
    session.commit()
```

Rode dentro do container: `docker compose exec backend python -m <seu_modulo>`. Daí em diante a
rodada aparece no seletor da tela, com todo o fluxo do analista funcionando. Se quiser rodar no
`docker compose up`, chame-o em `backend/app/seed/run.py` ou exponha um endpoint em
`backend/app/api/rounds.py`.

**b) Gerar o CSV (útil para comparar resultados).** Se o motor escrever um CSV no formato de
`docs/CONTEXTO_DESAFIO.md`, ele pode ser importado pela tela (botão **Importar rodada**), pela API
(`POST /api/rounds/import`) ou colocado em `seed/` com o nome `recomendacoes_rodada_AAAA-MM-DD.csv`
para o seed importar ao subir. O importador valida linha a linha e devolve os erros.

## 4. Regras importantes

- As regras R01–R12 (`docs/CONTEXTO_DESAFIO.md`) são responsabilidade do motor: bloquear preço
  abaixo do piso (R01), limitar a variação a 5% (R02), mandar para REVISAR ou marcar
  `requires_approval` quando a regra pedir, e explicar o motivo em `review_reasons`.
- O motor **recomenda**; quem decide é o analista. Não grave decisões nem altere preços vigentes.
- As decisões são append-only (um trigger no banco bloqueia UPDATE/DELETE em `decisions`).
- Mantenha os nomes de código em inglês e os textos ao usuário em português.

## 5. Como rodar

```bash
docker compose up --build    # db + backend + frontend; migrations e seed
open http://localhost:5173   # aplicação (sem rodada: a tela pede para importar uma)
open http://localhost:8000/docs
make test                    # pytest
make lint
```

Sem o arquivo de rodada, o seed carrega só usuários e a base da empresa, e a tela de Recomendações
mostra "Nenhuma rodada importada". **Os testes que dependem da rodada de exemplo são pulados**
(aparecem como `skipped`, com o motivo). Quando o motor gerar uma rodada, escreva testes para ele em
`backend/tests/` — por exemplo, verificando R01/R02 em todos os itens e uma recomendação por
SKU × canal.
