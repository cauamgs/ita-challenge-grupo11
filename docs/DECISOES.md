# Decisões de interpretação — v1

Registro das escolhas feitas onde o spec era ambíguo ou divergia dos dados. Mais recente no fim.

## Infraestrutura

- **D01 — Porta do Postgres.** O serviço `db` não publica porta no host (evita conflito com outros
  Postgres locais). Para acessar: `docker compose exec db psql -U popularpet`.
- **D02 — Banco de testes.** Os testes do backend usam um banco separado (`popularpet_test`), criado
  pelo script de init do container `db`. Rodam dentro do container: `make test`.
- **D03 — Formatação Python.** Usamos `ruff format` (compatível com black) em vez de black, para ter
  uma única ferramenta de lint + formatação.

## Dados e seed

- **D04 — Fonte da verdade é o CSV.** Onde os exemplos dos documentos divergem do CSV, vale o CSV:
  - `exige_aprovacao`: o CSV tem 52 itens (46 REVISAR + 6 MANTER), não 24 como no exemplo do resumo.
  - Motivos de REVISAR (resumo da rodada): no CSV dá campanha 18, cobertura curta 20, dados frágeis 6.
- **D05 — Contagem de motivos de revisão.** Um item REVISAR pode ter vários motivos (`; `). Cada item
  conta **uma vez em cada grupo** que aparece nos seus motivos (campanha, cobertura curta, dados
  frágeis); "outros" conta os itens que têm ao menos um motivo fora desses três grupos. Por isso a
  soma dos grupos pode passar do total de REVISAR.
- **D06 — Data do estoque.** A aba Estoque não tem data de referência; usamos a data de referência da
  aba Precos_Atuais (09/09/2026) em `stock_snapshot.reference_date`.
- **D07 — `is_strategic`.** A base não tem coluna de produto estratégico; todos ficam `false`.
- **D08 — SKU desconhecido na importação.** Importar um CSV com SKU que não existe em `products`
  falha com 422 (erro por SKU). A v1 não cria produtos a partir do CSV de recomendações.
- **D09 — Substituir rodada (`replace=true`).** Só é permitido se a rodada ainda não tem decisões; com
  decisões, retorna 409 (as decisões são append-only e não podem perder a recomendação de origem).
- **D10 — Append-only no banco.** Além do service nunca atualizar/apagar, um trigger em `decisions`
  bloqueia UPDATE e DELETE.

## API e regras derivadas

- **D11 — Status na lista.** `status` assume: `PENDENTE` (sem decisão), `ADIADA` (última decisão =
  ADIAR; conta como pendente), `APROVADA`, `EDITADA`, `REJEITADA` e `SEM_ACAO` (MANTER sem decisão:
  "sem ação necessária", não conta como pendente). Filtro "Pendente" = PENDENTE + ADIADA; filtro
  "Decidido" = APROVADA + EDITADA + REJEITADA; `SEM_ACAO` só aparece em "Todos".
- **D12 — "Maior valor em jogo" no resumo.** Considera só as sugestões de alteração (SUBIR/BAIXAR),
  que é o que o analista aplica diretamente. No seed isso dá PP-0020 na Loja física, como no exemplo
  do spec. (Considerando também REVISAR, o maior seria PP-0011, um item que vai para revisão.)
  A ordenação da lista por "valor em jogo" considera todos os itens, com MANTER no fim.
- **D13 — Ordenação por risco.** Por nível (Baixo < Médio < Alto) e, dentro do nível, por
  `risk_score`. Empates sempre desfeitos pela prioridade.
- **D14 — Datas das decisões.** O `created_at` de cada decisão é definido pela aplicação no momento
  do registro (e não por `now()` da transação), para que decisões feitas em sequência tenham ordem
  estável.

## Frontend

- **D15 — Rodada e analista.** A rodada ativa é estado da sessão (padrão: a mais recente) e vale para
  todas as telas; o analista escolhido fica em `localStorage`. Os filtros da lista ficam na URL com
  chaves em português (`canal`, `curva`, `recomendacao`, `risco`, `status`, `aprovacao`, `q`, `ordem`,
  `dir`, `pagina`) e o item aberto no drawer em `item`, para que o link possa ser compartilhado.
- **D16 — Paginação.** Paginação numerada de 25 itens (mais simples que rolagem infinita).
- **D17 — Regras citadas.** Os códigos R01–R12 que aparecem nos motivos e alertas são listados no
  bloco "Regras" do detalhe, com o texto da regra.

## Decisões do analista e exportação

- **D18 — Formato dos CSV exportados.** Mesmo formato do CSV de entrada: separador vírgula, ponto
  decimal, datas `AAAA-MM-DD HH:mm` no fuso de São Paulo, UTF-8 com BOM (para o Excel reconhecer os
  acentos). `variacao` = preço aplicado / preço atual − 1.
- **D19 — Campos por tipo de decisão.** APROVAR ignora qualquer `applied_price` enviado e grava o
  preço sugerido; REJEITAR e ADIAR gravam `applied_price` nulo. O motivo de rejeição precisa ser um
  dos cinco da lista do spec. Comentários vazios viram nulo.
- **D20 — Itens adiados no detalhe.** Um item adiado mostra quem adiou e quando, e os quatro botões
  continuam disponíveis (ele segue pendente). "Refazer decisão" aparece só para Aprovada, Editada e
  Rejeitada.
- **D21 — Avisos R01/R02 na edição.** Aparecem enquanto o analista digita (o botão muda para
  "Confirmar mesmo assim") e voltam na resposta da API, exibidos na notificação após salvar.

## Métricas

- **D22 — Base das métricas.** Todas as métricas são da rodada selecionada, com os filtros de canal e
  curva aplicados. Faixa competitiva e margem média usam os preços e margens que vieram na rodada.
  Faixa competitiva: denominador = itens com preço de mercado.
- **D23 — Tempo de revisão.** Itens decididos (Aprovada, Editada, Rejeitada) × 2 min; adiados
  contam como pendentes (0 min). Abaixo de 1 h é exibido em minutos.
- **D24 — Decisões por recomendação.** Além dos cinco estados do spec, o gráfico mostra "Sem ação
  (MANTER)" separado de "Pendente", coerente com D11.
- **D25 — Índice de preço.** As barras partem da linha de referência 100 (acima = mais caro que o
  mercado, abaixo = mais barato), em vez de partir de zero, para que diferenças de ±1 ponto fiquem
  visíveis sem truncar o eixo. No seed o índice por curva é praticamente igual nos três canais
  (é assim no CSV).
- **D26 — Cores dos gráficos.** Os gráficos de recomendação e decisão usam as cores das tags (como
  pede o spec), sempre com contorno, rótulo de categoria no eixo, legenda e valores escritos, porque
  verde e rosa claros não se distinguem para daltônicos. Os demais usam `purpleData`; a referência
  usa `lime`. Top 10 tem link para abrir o item na tela de Recomendações.

## Histórico e importação

- **D27 — Histórico.** Lista todas as decisões de todas as rodadas (inclusive as substituídas por
  "Refazer decisão"), mais recente primeiro; é o registro de auditoria. O período filtra pela data
  do registro no fuso de São Paulo, com as duas pontas inclusivas. Filtros na URL (`analista`,
  `decisao`, `canal`, `de`, `ate`).
- **D28 — Importação pela interface.** O botão "Importar rodada" fica na tela de Recomendações; a
  data vem da coluna `rodada_data`. Após importar, a rodada nova passa a ser a selecionada. Data já
  existente → 409 com opção "Substituir" (só sem decisões, D09). CSV inválido → 422 com a lista de
  erros por linha exibida no modal. O analista selecionado é gravado em `rounds.imported_by`.
