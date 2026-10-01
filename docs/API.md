# Contrato da API (FastAPI) — v1

Base: `/api`. JSON, UTF-8. Erros no formato `{ "detail": "mensagem em português" }`. Paginação por
`page` (1-based) e `page_size` (padrão 25, máx. 200), resposta `{ items, total, page, page_size }`.
Documentação automática em `/docs` (Swagger) deve funcionar.

## Usuários
- `GET /users` → lista de usuários ativos `[{ id, name, role }]`.

## Rodadas
- `GET /rounds` → `[{ id, round_date, source, created_at, counts: { total, SUBIR, BAIXAR, MANTER, REVISAR } }]`, mais recente primeiro.
- `GET /rounds/{id}/summary` → resumo da rodada:
  ```json
  {
    "round_date": "2026-09-09",
    "total": 120,
    "with_change": 58,
    "by_recommendation": { "SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46 },
    "review_reasons": { "campanha": 15, "cobertura_curta": 20, "dados_frageis": 6, "outros": 5 },
    "requires_approval": 24,
    "top_value_at_stake": { "sku": "PP-0020", "product": "Comedouro Inox M", "channel": "LOJA_FISICA", "value": 2011.0 },
    "decided": 0, "pending": 104,
    "summary_text": "120 itens · 58 com sugestão de alteração · 46 exigem revisão (15 por campanha, 20 por cobertura curta, 6 por dados frágeis) · 24 exigem aprovação. Maior valor em jogo: PP-0020 na Loja física."
  }
  ```
- `POST /rounds/import` (multipart `file`, query `replace=false`, header/campo `user_id`) → cria rodada
  a partir do CSV. 201 com `{ round_id, round_date, imported: 120 }`. 409 se já existir e `replace=false`.
  422 com lista de erros de validação por linha quando o CSV estiver inválido.

## Recomendações
- `GET /rounds/{id}/recommendations`
  - Filtros: `channel`, `abc_curve`, `recommendation`, `risk_level`, `status` (PENDENTE|DECIDIDO),
    `requires_approval` (bool), `q` (busca em sku/nome), `sort` (priority|variation|value_at_stake|risk),
    `order` (asc|desc), `page`, `page_size`.
  - Item:
    ```json
    {
      "id": "…", "priority": 1, "sku": "PP-0020", "product_name": "Comedouro Inox M",
      "category": "Acessórios", "abc_curve": "B", "channel": "LOJA_FISICA",
      "current_price": 220.71, "market_price": 215.79, "recommendation": "BAIXAR",
      "suggested_price": 215.79, "variation": -0.0223, "resulting_margin": 0.3556,
      "risk_level": "BAIXO", "requires_approval": false, "value_at_stake": 2011.0,
      "status": "PENDENTE", "last_decision": null
    }
    ```
- `GET /recommendations/{id}` → detalhe completo (todos os campos da tabela + `product`, `status`,
  `last_decision`, `decision_history` deste SKU×canal em todas as rodadas, `min_price_floor`).
- `POST /recommendations/{id}/decisions`
  ```json
  { "user_id": "…", "decision": "EDITAR", "applied_price": 214.90, "rejection_reason": null, "comment": "…" }
  ```
  Validações: `applied_price` obrigatório e > 0 para EDITAR; `rejection_reason` obrigatório para
  REJEITAR; APROVAR grava `applied_price = suggested_price`. Resposta 201 com a decisão e
  `warnings: ["Preço abaixo do piso de margem mínima (R$ 96,50)", "Variação acima de 5% (R02)"]`
  quando aplicável (avisos não bloqueiam). Sempre cria novo registro (refazer = novo POST).
- `GET /rounds/{id}/export` → CSV das decisões vigentes APROVAR/EDITAR (`text/csv`, `Content-Disposition`).

## Métricas
- `GET /rounds/{id}/metrics?channel=&abc_curve=`
  ```json
  {
    "acceptance_rate": { "value": 0.72, "numerator": 36, "denominator": 50, "target": 0.70 },
    "estimated_review_hours": { "value": 1.7, "target": 6 },
    "in_competitive_band": { "value": 0.65, "target": 0.80 },
    "avg_gross_margin": { "value": 0.318, "target": 0.325 },
    "reversal_rate": { "value": null, "target": 0.03, "note": "não disponível na v1" },
    "recommendation_distribution": { "SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46 },
    "price_index_by_curve": { "A": 101.0, "B": 101.8, "C": 101.3 },
    "decisions_by_recommendation": { "SUBIR": { "APROVADA": 0, "EDITADA": 0, "REJEITADA": 0, "ADIADA": 0, "PENDENTE": 20 }, "...": {} },
    "rejection_reasons": { "Discordo da referência de mercado": 0 },
    "top_value_at_stake": [ { "sku": "…", "product_name": "…", "channel": "…", "recommendation": "…", "variation": -0.02, "value_at_stake": 2011.0, "status": "PENDENTE" } ]
  }
  ```

## Histórico
- `GET /decisions?user_id=&decision=&channel=&date_from=&date_to=&page=&page_size=` → decisões com
  dados da recomendação e do produto embutidos.
- `GET /decisions/export` (mesmos filtros) → CSV.

## Saúde
- `GET /health` → `{ "status": "ok", "db": "ok" }`.

## Pontos de extensão (v2)
- `backend/app/engine/base.py`: `class RecommendationEngine(Protocol): def run(self, round_date: date) -> list[RecommendationIn]`.
  v1: `CsvImportEngine(file)`; v2: motor real.
- `backend/app/explain/base.py`: `class Explainer(Protocol): def explain(self, rec: Recommendation) -> str`.
  v1: `StaticExplainer` (devolve `justification`); v2: LLM.
