# Modelo de dados (PostgreSQL)

Convenções: nomes em inglês, snake_case, `id` UUID (`gen_random_uuid()`), `created_at timestamptz
default now()`. Valores monetários `numeric(12,2)`; percentuais como fração em `numeric(8,4)`
(0.2350 = 23,5%). Enums como tipos PostgreSQL.

```sql
create type channel_t        as enum ('LOJA_FISICA','ECOMMERCE','MARKETPLACE');
create type recommendation_t as enum ('SUBIR','BAIXAR','MANTER','REVISAR');
create type risk_t           as enum ('BAIXO','MEDIO','ALTO');
create type decision_t       as enum ('APROVAR','EDITAR','REJEITAR','ADIAR');
create type user_role_t      as enum ('ANALISTA','GESTOR');

-- Usuários (sem autenticação na v1)
create table users (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  role        user_role_t not null,
  active      boolean not null default true,
  created_at  timestamptz not null default now()
);

-- Catálogo (da aba Produtos)
create table products (
  sku            text primary key,              -- 'PP-0001'
  name           text not null,
  category       text not null,
  brand          text not null,
  abc_curve      char(1) not null check (abc_curve in ('A','B','C')),
  status         text not null,                 -- 'Ativo' | 'Descontinuando'
  is_strategic   boolean not null default false,
  created_at     timestamptz not null default now()
);

-- Preço e custo vigentes por SKU × canal (abas Precos_Atuais + Custos_Margens)
create table product_channel_state (
  id               uuid primary key default gen_random_uuid(),
  sku              text not null references products(sku),
  channel          channel_t not null,
  reference_date   date not null,
  current_price    numeric(12,2) not null,
  replacement_cost numeric(12,2) not null,
  taxes            numeric(12,2) not null default 0,
  freight          numeric(12,2) not null default 0,
  channel_fee      numeric(8,4)  not null default 0,   -- fração (0.12 = 12%)
  min_margin       numeric(8,4)  not null,
  target_margin    numeric(8,4)  not null,
  unique (sku, channel, reference_date)
);

-- Estoque (aba Estoque) — único por SKU na base
create table stock_snapshot (
  id                 uuid primary key default gen_random_uuid(),
  sku                text not null references products(sku),
  reference_date     date not null,
  quantity           integer not null,
  coverage_days      numeric(8,1),
  open_po_quantity   integer not null default 0,
  expected_receipt   date,
  location           text,
  unique (sku, reference_date)
);

-- Rodadas do motor
create table rounds (
  id            uuid primary key default gen_random_uuid(),
  round_date    date not null unique,
  source        text not null,                  -- 'csv_import' | 'engine' (v2)
  source_file   text,
  imported_by   uuid references users(id),
  created_at    timestamptz not null default now()
);

-- Recomendações (uma por SKU × canal × rodada) — espelho do CSV
create table recommendations (
  id                   uuid primary key default gen_random_uuid(),
  round_id             uuid not null references rounds(id) on delete cascade,
  priority             integer not null,
  sku                  text not null references products(sku),
  channel              channel_t not null,
  current_price        numeric(12,2) not null,
  market_price         numeric(12,2),
  lowest_valid_competitor numeric(12,2),
  cost                 numeric(12,2) not null,
  current_margin       numeric(8,4) not null,
  min_margin           numeric(8,4) not null,
  target_margin        numeric(8,4) not null,
  net_margin           numeric(8,4),
  stock_qty            integer,
  coverage_days        numeric(8,1),
  sales_trend_month    numeric(8,4),
  sales_var_12m        numeric(8,4),
  recommendation       recommendation_t not null,
  suggested_price      numeric(12,2) not null,
  variation            numeric(8,4) not null,           -- suggested/current - 1
  resulting_margin     numeric(8,4) not null,
  risk_level           risk_t not null,
  risk_score           numeric(5,1),
  data_confidence      numeric(5,3),
  requires_approval    boolean not null default false,
  est_monthly_revenue  numeric(14,2),
  est_monthly_impact   numeric(14,2),
  justification        text not null,
  review_reasons       text[] not null default '{}',   -- split de motivos_revisao por '; '
  data_alerts          text[] not null default '{}',   -- split de alertas_dados por '; '
  created_at           timestamptz not null default now(),
  unique (round_id, sku, channel)
);
create index on recommendations (round_id, priority);
create index on recommendations (round_id, recommendation);

-- Decisões do analista — append-only (nunca update/delete)
create table decisions (
  id                   uuid primary key default gen_random_uuid(),
  recommendation_id    uuid not null references recommendations(id),
  user_id              uuid not null references users(id),
  decision             decision_t not null,
  applied_price        numeric(12,2),                   -- APROVAR: = suggested; EDITAR: informado; demais: null
  rejection_reason     text,                            -- obrigatório quando REJEITAR
  comment              text,
  -- snapshot para auditoria, mesmo que a recomendação mude
  snapshot_recommendation recommendation_t not null,
  snapshot_suggested_price numeric(12,2) not null,
  snapshot_current_price   numeric(12,2) not null,
  created_at           timestamptz not null default now()
);
create index on decisions (recommendation_id, created_at desc);
```

## Regras derivadas (implementar em services, não em SQL)

- **Decisão vigente** de uma recomendação = a mais recente em `decisions` (por `created_at`).
- **Status na lista**: `PENDENTE` (sem decisão, ou última = ADIAR → mostrar "Adiada" mas contar como
  pendente), `APROVADA`, `EDITADA`, `REJEITADA`.
- **Valor em jogo** = `est_monthly_revenue × |variation|` (null/“—” quando MANTER).
- **Piso de margem** = `cost / (1 − min_margin)` — usado só para o **aviso** na edição (R01).
- **Aceite** (métrica primária): numerador = decisões vigentes APROVAR, ou EDITAR com
  `|applied_price − suggested_price| ≤ 0.01 × current_price`, em recomendações SUBIR/BAIXAR;
  denominador = recomendações SUBIR/BAIXAR com decisão vigente ≠ ADIAR.
- **Mapeamento do CSV**: `canal` "Loja física" → LOJA_FISICA, "E-commerce" → ECOMMERCE,
  "Marketplace" → MARKETPLACE; `nivel_risco` "Baixo/Médio/Alto" → BAIXO/MEDIO/ALTO.

## Seed

1. `users`: Ana Souza (ANALISTA), Bruno Lima (ANALISTA), Carla Menezes (GESTOR).
2. `products`, `product_channel_state`, `stock_snapshot` a partir de `seed/base_popular_pet.xlsx`
   (abas Produtos, Precos_Atuais, Custos_Margens, Estoque; `header=2`; datas `dd/mm/aaaa`).
3. `rounds` + `recommendations` a partir de `seed/recomendacoes_rodada_2026-09-09.csv`.
4. Idempotente: usar `on conflict do nothing` / verificar existência antes de inserir.
