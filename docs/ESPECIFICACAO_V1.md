# Especificação funcional — v1

## 1. Escopo

### Dentro da v1
1. Importar a base da empresa (xlsx) e as recomendações de uma rodada (csv) para o PostgreSQL.
2. Tela **Recomendações**: lista priorizada, filtros, detalhe por item, ações do analista.
3. Tela **Métricas**: indicadores da rodada e da carteira, lidos do banco (recomendações + decisões).
4. Tela **Histórico**: registro de auditoria com todas as decisões.
5. Exportação das decisões aprovadas/editadas em CSV.
6. Seletor de analista (sem login).

### Fora da v1 (deixar pontos de extensão)
- Motor de decisão (cálculo de recomendação, preço, risco, prioridade). Interface `RecommendationEngine`
  com uma implementação `CsvImportEngine`.
- IA generativa (justificativa em linguagem natural, assistente de perguntas, resumo da rodada).
  Interface `Explainer` com implementação `StaticExplainer` que devolve o texto do CSV.
- Aplicação do preço no ERP/e-commerce. A v1 só exporta CSV.
- Autenticação e perfis. Só o seletor de nome.
- Múltiplas rodadas simultâneas na interface. O modelo suporta várias rodadas; a interface mostra a mais
  recente, com seletor de rodada simples.

## 2. Papéis (v1)

- **Analista**: usa a tela de Recomendações; decide.
- **Gestor**: usa a tela de Métricas; na v1 não há permissão diferenciada, apenas o nome.

Lista fixa de usuários no seed: `Ana Souza (Analista)`, `Bruno Lima (Analista)`, `Carla Menezes (Gestora)`.

## 3. Tela: Recomendações (rota `/recomendacoes`)

### 3.1 Cabeçalho
- Logo Popular Pet à esquerda, título "Recomendações de preço", seletor de rodada (data), seletor de
  analista à direita.

### 3.2 Resumo da rodada (faixa verde-clara, abaixo do cabeçalho)
Texto gerado **pelo backend a partir de contagens** (não por IA), no formato:
> **Resumo da rodada:** 120 itens · 58 com sugestão de alteração · 46 exigem revisão (15 por campanha,
> 20 por cobertura curta, 6 por dados frágeis) · 24 exigem aprovação. Maior valor em jogo: PP-0020 na
> Loja física.

Os agrupamentos de motivo de REVISAR vêm de palavras-chave em `motivos_revisao`: "campanha" → campanha;
"cobertura" → cobertura curta; "dados" ou "confiança" → dados frágeis; demais → outros.

### 3.3 Filtros (uma linha)
- Canal (Todos / Loja física / E-commerce / Marketplace)
- Curva ABC (Todas / A / B / C)
- Recomendação (Todas / SUBIR / BAIXAR / MANTER / REVISAR)
- Risco (Todos / Baixo / Médio / Alto)
- Status da decisão (Todos / Pendente / Decidido)
- Checkbox "Só exige aprovação"
- Busca por SKU ou nome do produto
- Botão "Exportar aprovadas" (CSV) à direita

Filtros persistem na URL (query string) para poder compartilhar.

### 3.4 Lista (tabela)
Colunas, nesta ordem: `#` (prioridade), `SKU · Produto`, `Canal`, `Preço atual`, `Preço de mercado`,
`Recomendação` (tag colorida), `Preço sugerido`, `Variação` (%), `Margem resultante` (%), `Risco` (tag),
`Valor em jogo` (R$/mês = receita_mensal_est × |variacao|; para MANTER mostrar "—"), `Aprovação`
(ícone quando exige), `Decisão` (tag com o estado: Pendente / Aprovada / Editada / Rejeitada / Adiada).

- Ordenação padrão: prioridade crescente. Permitir ordenar por variação, valor em jogo, risco.
- Paginação: 25 por página (ou scroll com carregamento; escolha o mais simples).
- Linhas com decisão registrada ficam com fundo levemente cinza.
- Clique na linha abre o **painel de detalhe** (drawer lateral direito ou seção expandida abaixo;
  drawer é preferível).

### 3.5 Painel de detalhe
Cabeçalho: `SKU · Produto · Canal · [tag Recomendação] · [tag Risco]`.

Blocos, nesta ordem:
1. **Justificativa** — texto de `justificativa` (fonte normal, parágrafo).
2. **Números** — grade 2 colunas: preço atual, preço de mercado, menor concorrente válido, preço
   sugerido, variação, custo, margem atual, margem mínima, margem alvo, margem resultante, margem
   líquida do canal, estoque, cobertura (dias), tendência de vendas (%/mês), variação 12 m, confiança
   dos dados (%), receita mensal estimada, impacto mensal estimado (com rótulo "estimativa").
3. **Motivos de revisão** — lista (só quando houver).
4. **Alertas de dados** — lista (só quando houver).
5. **Regras** — se `exige_aprovacao`, mostrar aviso "Exige aprovação de gestor".
6. **Decisão** — se pendente: quatro botões (Aprovar / Editar / Rejeitar / Adiar) e campo de
   comentário opcional. Se já decidida: mostrar decisão, autor, data/hora, preço aplicado e comentário,
   com botão "Refazer decisão" (cria um novo registro; nunca apaga o anterior).
7. **Histórico do item** — decisões anteriores deste SKU × canal (todas as rodadas).

Regras das ações:
- **Aprovar**: grava `decision=APROVAR`, `applied_price=preco_sugerido`.
- **Editar**: abre campo numérico com o preço; validações: obrigatório, > 0, e **aviso** (não bloqueio)
  se o preço editado ficar abaixo do piso de margem mínima (`custo / (1 − margem_minima)`) ou se a
  variação em relação ao preço atual passar de 5% (R01 e R02). Grava `decision=EDITAR`,
  `applied_price=<valor>`.
- **Rejeitar**: motivo obrigatório (seleção: "Discordo da referência de mercado", "Estoque/reposição",
  "Estratégia comercial", "Dados incorretos", "Outro") + comentário opcional. Grava `decision=REJEITAR`.
- **Adiar**: comentário opcional; grava `decision=ADIAR`. Item continua aparecendo como pendente com
  marcação "adiado".
- Para itens MANTER, os botões existem (o analista pode discordar e editar), mas a lista trata MANTER
  sem decisão como "sem ação necessária" (não conta como pendente nas métricas).
- Toda decisão grava: usuário, timestamp, recomendação original, preço sugerido, preço aplicado,
  motivo, comentário. **Registros são imutáveis** (append-only).

### 3.6 Exportar aprovadas
CSV com: sku, produto, canal, preco_atual, preco_aplicado, variacao, decisao, analista, data_hora,
comentario. Inclui APROVAR e EDITAR da rodada selecionada. Nome do arquivo:
`decisoes_<rodada>_<AAAA-MM-DD_HHMM>.csv`.

## 4. Tela: Métricas (rota `/metricas`)

Filtros no topo: rodada, canal, curva.

### 4.1 Cards (linha de 5)
| Card | Cálculo (v1) | Meta exibida |
|---|---|---|
| Aceite das recomendações | (APROVAR + EDITAR com |preço aplicado − sugerido| ≤ 1% do preço atual) ÷ (SUBIR+BAIXAR com decisão), na rodada | ≥ 70% |
| Tempo estimado de revisão | nº de itens decididos × 2 min + pendentes × 0 (mostrar "estimado") | ≤ 6 h/semana |
| SKUs na faixa competitiva | % de SKU×canal com |preco_atual/preco_mercado − 1| ≤ 2% | ≥ 80% |
| Margem bruta média | média de `margem_atual` ponderada por `receita_mensal_est` | ≥ 32,5% |
| Taxa de reversão | "—" na v1 (sem histórico); mostrar "não disponível na v1" | ≤ 3% |

Se o denominador do aceite for zero, mostrar "—" e "nenhuma decisão registrada".

### 4.2 Gráficos (linha de 2, depois linha de 2)
1. **Distribuição das recomendações** — barras horizontais: SUBIR, BAIXAR, MANTER, REVISAR (contagem),
   com cores das tags.
2. **Índice de preço por curva** — barras: média de `preco_atual/preco_mercado × 100` por curva A/B/C,
   com linha de referência em 100.
3. **Decisões do analista** — barras empilhadas por recomendação: Aprovada / Editada / Rejeitada /
   Adiada / Pendente.
4. **Motivos de rejeição** — barras: contagem por motivo.

Gráficos com Recharts ou SVG próprio; cores da marca (ver UI_GUIDE). Sem eixo duplo.

### 4.3 Tabela "Top 10 por valor em jogo"
SKU, produto, canal, recomendação, variação, valor em jogo, decisão.

## 5. Tela: Histórico (rota `/historico`)

Tabela de todas as decisões (todas as rodadas), mais recente primeiro: data/hora, analista, SKU,
produto, canal, recomendação, preço sugerido, decisão, preço aplicado, motivo, comentário. Filtros:
analista, decisão, canal, período. Exportar CSV.

## 6. Importação e rodadas

- `POST /api/rounds/import` recebe o CSV de recomendações (multipart) e cria uma rodada com a data do
  campo `rodada_data`. Se já existir rodada na mesma data, retornar 409 (a menos que `?replace=true`).
- No `docker compose up`, um job de seed importa `seed/base_popular_pet.xlsx` (produtos, canais,
  preços, custos, estoque) e `seed/recomendacoes_rodada_2026-09-09.csv`, além dos usuários. O seed é
  idempotente.
- Botão "Importar rodada" na tela de Recomendações (upload simples) — útil para a v2 gerar novos CSVs.

## 7. Regras de interface transversais

- Moeda em `R$ 1.234,56`; percentuais com 1 casa (`+2,3%`, com sinal para variação); datas
  `dd/mm/aaaa` e `dd/mm/aaaa HH:mm`.
- Tags de recomendação e risco com as cores do UI_GUIDE; nunca só cor: sempre com texto.
- Estados vazios e de carregamento em todas as listas.
- Layout responsivo até ~1024px; abaixo disso, tabela com rolagem horizontal.
- Acessibilidade básica: botões com rótulo, contraste, foco visível.

## 8. Critérios de aceite da v1

1. `docker compose up` do zero sobe db, backend e frontend; ao abrir `http://localhost:5173` a tela de
   Recomendações mostra 120 itens da rodada 2026-09-09 com o resumo correto (38/20/16/46).
2. É possível filtrar, abrir o detalhe, aprovar, editar (com aviso de R01/R02), rejeitar (com motivo)
   e adiar; a decisão aparece na linha e no histórico; refazer decisão cria novo registro.
3. Exportar aprovadas gera CSV correto.
4. Métricas refletem as decisões em tempo real (após decidir, o aceite muda).
5. Importar um novo CSV cria uma nova rodada e o seletor permite alternar.
6. Testes do backend passam; lint do frontend passa.
