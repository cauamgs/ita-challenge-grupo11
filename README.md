# Popular Pet · Precificação Inteligente — Protótipo v1 (Grupo 11)

Sistema de recomendação de preço para a Popular Pet. Para cada SKU em cada canal (Loja física,
E-commerce, Marketplace), uma rodada traz uma recomendação — **SUBIR, BAIXAR, MANTER ou REVISAR** —
com preço sugerido, nível de risco e justificativa. O analista de pricing **vê, filtra, prioriza e
decide** (aprovar, editar, rejeitar ou adiar) e o painel de métricas acompanha a carteira e o efeito
das decisões. Nenhum preço é alterado sem decisão humana registrada.

O motor de decisão (o cálculo das recomendações) ainda não está neste repositório: as rodadas entram
por importação de CSV no formato da saída do motor (ver `docs/HANDOFF_MOTOR.md`). A base de produtos
vem de uma **integração simulada com o ERP** — sincronização manual, automática ou por arquivo.

## Como subir

```bash
cp .env.example .env        # opcional: só se quiser trocar portas/senhas
docker compose up --build   # sobe db, backend e frontend; aplica migrations e roda o seed
open http://localhost:5173  # aplicação  ·  API/Swagger: http://localhost:8000/docs
```

Na primeira subida o seed carrega 3 usuários e faz a **sincronização inicial com o ERP** (40
produtos, 120 preços por canal, 40 estoques e o histórico de preços). Se houver arquivos `seed/recomendacoes_rodada_*.csv`,
importa também essas rodadas (a de 09/09/2026 tem 120 recomendações: 38 BAIXAR, 20 SUBIR, 16 MANTER, 46 REVISAR). O seed
é idempotente: rodar de novo não duplica nada. Para quem vai implementar o motor de decisão, ver
`docs/HANDOFF_MOTOR.md`.

| Comando | O que faz |
|---|---|
| `make up` / `make down` | sobe / derruba os serviços |
| `make reset` | apaga o banco (`down -v`) e sobe do zero |
| `make test` | testes do backend (pytest, banco `popularpet_test` separado) |
| `make lint` | ruff + ruff format, ESLint + Prettier + TypeScript |
| `make format` | formata backend e frontend |
| `make seed` | roda o seed de novo (idempotente) |
| `make logs` | acompanha os logs |

O Postgres não publica porta no host; para consultar: `docker compose exec db psql -U popularpet`.

## Telas

- **Início** (`/inicio`, tela inicial): dashboard da plataforma — situação da base do ERP, KPIs da
  rodada e da carteira, atalhos para as análises já filtradas (alto risco, exige aprovação, maior
  valor em jogo, métricas, histórico de preços, analistas), progresso da rodada, decisões por dia,
  alterações de preço por mês, pendentes de maior valor, atividade recente e analistas.
- **Recomendações** (`/recomendacoes`): resumo da rodada, filtros (canal, curva, recomendação, risco,
  status, só exige aprovação, busca) guardados na URL, tabela ordenável com paginação de 25, drawer de
  detalhe (justificativa, números, motivos de revisão, alertas de dados, regras R01–R12 citadas,
  aviso de aprovação de gestor), decisão e histórico do item. Botões **Importar rodada** e
  **Exportar aprovadas**.
- **Métricas** (`/metricas`): aceite das recomendações (métrica primária, meta ≥ 70%), tempo estimado
  de revisão, SKUs na faixa competitiva, margem bruta média, taxa de reversão (n/d na v1);
  distribuição das recomendações, índice de preço por curva, decisões por recomendação, motivos de
  rejeição; top 10 por valor em jogo. Filtros de rodada, canal e curva.
- **Produtos** (`/produtos`): catálogo vindo do ERP com preço por canal, última alteração de preço,
  estoque e pendências; filtros e ordenação por alteração mais recente. **Detalhe do SKU**
  (`/produtos/:sku`): preço, custo, piso e margens por canal, estoque, gráfico da evolução do preço,
  histórico de alterações (aumentos, reduções, registro inicial, com motivo e origem) e todas as
  recomendações/decisões do SKU.
- **Analistas** (`/analistas`): histórico de análises por analista — decisões, tipo, aceite pessoal,
  rodadas e última atividade; o detalhe traz decisões por dia, perfil, motivos de rejeição e a lista
  de análises com exportação CSV.
- **Histórico** (`/historico`): registro de auditoria de todas as decisões de todas as rodadas, com
  filtros de analista, decisão, canal e período, e exportação CSV.
- **Integração ERP** (`/erp`): situação da integração, **Sincronizar agora**, **Importar arquivo do
  ERP** (.xlsx), **sincronização automática** (diária, semanal ou mensal em dia fixo — ex.: todo dia
  10 às 06:00 — com prévia da próxima execução) e histórico de todas as sincronizações.

O analista é escolhido no seletor do topo (sem login); toda decisão grava esse nome.

## Fluxo do analista

1. Abrir a rodada (a mais recente vem selecionada) e filtrar/priorizar — a ordem padrão é a
   prioridade da rodada (maior valor em jogo primeiro).
2. Clicar na linha para abrir o detalhe e decidir:
   - **Aprovar** grava o preço sugerido;
   - **Editar** pede o novo preço e avisa (sem bloquear) se ficar abaixo do piso de margem mínima
     (R01) ou variar mais de 5% sobre o preço atual (R02);
   - **Rejeitar** exige um motivo;
   - **Adiar** mantém o item como pendente.
3. **Refazer decisão** cria um novo registro — as decisões são append-only (um trigger no banco
   bloqueia UPDATE e DELETE em `decisions`).
4. **Exportar aprovadas** baixa `decisoes_<rodada>_<AAAA-MM-DD_HHMM>.csv` com as decisões vigentes
   Aprovar/Editar, para aplicação nos sistemas de venda (fora do escopo da v1).

## Integração com o ERP (simulada)

O ERP da Popular Pet é simulado pela planilha `seed/base_popular_pet.xlsx` (variável
`ERP_SOURCE_FILE` para usar outro arquivo). Cada sincronização valida a planilha inteira, atualiza
cadastro, preço/custos por canal e estoque, registra cada mudança de preço no histórico do SKU e fica
gravada com status, contagens e mensagem. Três formas de sincronizar:

- **Manual:** botão "Sincronizar agora" na tela Integração ERP (`POST /api/erp/sync`).
- **Automática:** configurada na mesma tela — diária, semanal (dia da semana) ou mensal (dia 1–28),
  num horário; o backend verifica a agenda a cada 30 s (`SCHEDULER_INTERVAL_SECONDS`).
- **Arquivo:** "Importar arquivo do ERP" com uma planilha no mesmo layout (`POST /api/erp/import`) —
  edite preços na planilha para simular alterações vindas do ERP.

## Como importar uma rodada

Pela interface: **Recomendações → Importar rodada**, escolher o CSV. Pela API:

```bash
curl -F "file=@recomendacoes_rodada_2026-09-16.csv" http://localhost:8000/api/rounds/import
```

- O CSV segue as colunas descritas em `docs/CONTEXTO_DESAFIO.md` ("O arquivo de recomendações");
  a data da rodada vem de `rodada_data`. Arquivos `seed/recomendacoes_rodada_*.csv` são importados
  pelo seed e ficam fora do git (`.gitignore`).
- `201` cria a rodada; `409` se já existir rodada na data (`?replace=true` substitui, desde que ela
  ainda não tenha decisões); `422` traz a lista de erros por linha (coluna ausente, valor inválido,
  SKU × canal duplicado, SKU fora do cadastro).
- O seletor de rodada no topo alterna entre as rodadas importadas.

## Arquitetura

```
docker-compose.yml   db (postgres:16) · backend (FastAPI :8000) · frontend (Vite :5173, proxy /api)
backend/
  app/api/           routers FastAPI (contrato em docs/API.md) e tratamento de erros em português
  app/services/      regras derivadas: status vigente, valor em jogo, piso de margem, resumo,
                     decisões e avisos R01/R02, aceite e métricas, exportações, sincronização
                     com o ERP (erp_sync), agenda (erp_schedule), produtos, analistas, dashboard
  app/scheduler.py   laço em segundo plano que roda a sincronização automática
  app/repositories/  consultas SQLAlchemy (decisão vigente = mais recente por recomendação)
  app/models/        models SQLAlchemy 2 (schema em docs/DATA_MODEL.md)
  app/schemas/       modelos Pydantic v2 de entrada/saída
  app/engine/        ponto de extensão do motor (RecommendationEngine, CsvImportEngine)
  app/explain/       ponto de extensão da IA generativa (Explainer, StaticExplainer)
  app/seed/          seed idempotente (usuários + sincronização inicial com o ERP + CSVs de rodada)
  alembic/           migrations (nada de create_all)
  tests/             pytest: seed, importação, API de leitura, decisões, métricas, histórico
frontend/src/
  app/               App, rotas, sessão (analista e rodada)
  pages/             Início, Recomendações, Métricas, Produtos, Analistas, Histórico, Integração ERP
  components/        AppShell, Tag, Button, Drawer, Modal, Table, gráficos (Recharts)…
  api/               cliente HTTP, tipos e hooks TanStack Query
  lib/               formatação pt-BR (moeda, %, datas), rótulos, regras R01–R12
```

Identidade visual (roxo `#5E3A85`, verde-lima `#B4C805`, cores de tags) configurada como tokens do
Tailwind conforme `docs/UI_GUIDE.md`. Fonte Inter servida localmente via `@fontsource/inter`.

## Pontos de extensão (v2)

- **Motor de decisão** — `backend/app/engine/base.py`:

  ```python
  class RecommendationEngine(Protocol):
      source: str                       # gravado em rounds.source ('engine' na v2)
      def run(self, round_date: date) -> list[RecommendationIn]: ...
  ```

  A v1 usa `CsvImportEngine`. Um motor real implementa o mesmo protocolo e é executado com
  `services.rounds.run_engine(session, engine, round_date)` — telas, decisões e métricas não mudam.
- **IA generativa** — `backend/app/explain/base.py`: `Explainer.explain(rec) -> str`. A v1 usa
  `StaticExplainer` (devolve a justificativa do CSV); trocar em `app/explain/get_explainer()`.
- **Autenticação** — a sessão do frontend (`src/app/session.tsx`) concentra o usuário atual; trocar
  o seletor por login não afeta o restante. O backend já recebe `user_id` em cada decisão.

## O que fica para a v2

- Motor de decisão (cálculo de recomendação, preço sugerido, risco e prioridade).
- IA generativa: justificativa em linguagem natural, assistente de perguntas, resumo da rodada.
- Login, perfis e fluxo de aprovação do gestor (na v1 "exige aprovação" é só sinalizado).
- Aplicação do preço no ERP/e-commerce (a v1 exporta CSV) e, com isso, a taxa de reversão.

## Critérios de aceite da v1 (ESPECIFICACAO_V1 §8)

| # | Critério | Como verificar |
|---|---|---|
| 1 | `docker compose up` do zero sobe tudo; 120 itens da rodada 09/09/2026 com resumo 38/20/16/46 | `make reset` e abrir http://localhost:5173 |
| 2 | Filtrar, abrir detalhe, aprovar, editar (aviso R01/R02), rejeitar (motivo), adiar; decisão na linha e no histórico; refazer cria novo registro | tela Recomendações; `tests/test_decisions.py` |
| 3 | Exportar aprovadas gera CSV correto | botão "Exportar aprovadas"; `test_export_current_approved_and_edited` |
| 4 | Métricas refletem as decisões em tempo real | decidir e abrir Métricas; `tests/test_metrics.py` |
| 5 | Importar novo CSV cria nova rodada e o seletor alterna | "Importar rodada"; `tests/test_history_import.py` |
| 6 | Testes do backend passam; lint do frontend passa | `make test` e `make lint` |

## Documentação

Escopo, regras e contratos em `docs/`. As interpretações adotadas onde o spec era
ambíguo ou divergia dos dados estão em `docs/DECISOES.md` — por exemplo, o CSV tem 52 itens que
exigem aprovação (não 24 como no exemplo) e vale o CSV.
