# Plano de tarefas — v1

Execute na ordem. Cada etapa termina com um commit e algo demonstrável. Marque as caixas conforme
concluir e registre desvios em `docs/DECISOES.md`.

## Etapa 0 — Esqueleto e infraestrutura
- [x] Estrutura de pastas:
  ```
  backend/   (FastAPI) app/{api,services,repositories,models,schemas,engine,explain,seed}, alembic/, tests/
  frontend/  (Vite + React + TS) src/{app,pages,components,lib,api}
  docker-compose.yml · .env.example · README.md · Makefile (up, down, logs, test, seed)
  ```
- [x] `docker-compose.yml`: `db` (postgres:16, volume, healthcheck), `backend` (depende do db saudável;
      roda `alembic upgrade head` e o seed antes do `uvicorn --reload`), `frontend` (Vite dev server em
      5173 com proxy `/api` → backend:8000).
- [x] `GET /api/health` respondendo; página React "Popular Pet" com AppShell vazio e tokens do
      UI_GUIDE configurados no Tailwind.
- [x] README com "como subir" em 3 comandos.
- **Demonstrável:** `docker compose up` → frontend abre com a barra roxa e o backend responde `/api/health`.

## Etapa 1 — Modelo de dados e seed
- [x] Models SQLAlchemy + migration Alembic conforme `DATA_MODEL.md`.
- [x] Seed idempotente: usuários; produtos/estado por canal/estoque a partir do xlsx; rodada +
      recomendações a partir do CSV (usar `CsvImportEngine`).
- [x] Testes: seed roda duas vezes sem duplicar; contagens (40 produtos, 120 estados, 120 recomendações;
      38/20/16/46).
- **Demonstrável:** `select count(*) from recommendations` = 120 após `docker compose up`.

## Etapa 2 — API de leitura
- [x] `GET /users`, `GET /rounds`, `GET /rounds/{id}/summary`, `GET /rounds/{id}/recommendations`
      (filtros, ordenação, paginação), `GET /recommendations/{id}`.
- [x] Cálculo de `value_at_stake`, `status`, `min_price_floor` em services.
- [x] Testes de endpoint (httpx + pytest) para filtros e resumo.
- **Demonstrável:** Swagger em `/docs` com os endpoints funcionando sobre o seed.

## Etapa 3 — Tela de Recomendações (leitura)
- [x] AppShell com abas, seletor de rodada e de analista (persistir analista em localStorage).
- [x] Caixa de resumo da rodada.
- [x] Filtros sincronizados com a URL; tabela com tags, ordenação e paginação; estados vazio/carregando.
- [x] Drawer de detalhe com justificativa, números, motivos, alertas e aviso de aprovação.
- **Demonstrável:** navegar, filtrar e abrir detalhes de qualquer item.

## Etapa 4 — Decisões
- [x] `POST /recommendations/{id}/decisions` com validações e avisos (R01/R02); append-only.
- [x] Botões Aprovar / Editar / Rejeitar / Adiar no drawer; modal de edição com aviso; modal de
      rejeição com motivo; comentário opcional.
- [x] Atualização otimista da linha e do resumo (TanStack Query invalidation).
- [x] Histórico do item no drawer; "Refazer decisão".
- [x] `GET /rounds/{id}/export` e botão "Exportar aprovadas".
- [x] Testes: regras de validação, aceite calculado, exportação.
- **Demonstrável:** fluxo completo do analista, com decisão refletida na lista e no CSV exportado.

## Etapa 5 — Métricas
- [x] `GET /rounds/{id}/metrics` com todos os campos do contrato.
- [x] Tela de Métricas: 5 cards, 4 gráficos (Recharts), tabela Top 10; filtros de rodada/canal/curva.
- [x] Cores da marca nos gráficos; legenda quando houver 2 séries; sem eixo duplo.
- **Demonstrável:** decidir alguns itens e ver o aceite e as barras mudarem.

## Etapa 6 — Histórico e importação
- [x] `GET /decisions` (+ export) e tela de Histórico com filtros.
- [x] `POST /rounds/import` e botão "Importar rodada" (upload); seletor de rodada alterna entre elas.
- [x] Teste: importar o mesmo CSV com data alterada cria segunda rodada.
- **Demonstrável:** duas rodadas no seletor; histórico consolidado.

## Etapa 7 — Acabamento
- [x] Revisão de textos (pt-BR), formatação de moeda/percentual/data, responsividade a 1024px.
- [x] Lint (ruff, eslint), formatação (black/prettier), testes verdes.
- [x] `docker compose down -v && docker compose up` do zero funcionando.
- [x] README final: arquitetura, como rodar, como importar uma rodada, pontos de extensão (engine,
      explainer), o que fica para a v2.

## Definição de pronto (v1)
Todos os critérios de aceite de `ESPECIFICACAO_V1.md` §8 atendidos e documentados no README.
