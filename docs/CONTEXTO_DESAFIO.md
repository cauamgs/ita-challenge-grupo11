# Contexto do desafio

## A empresa e o problema

A Popular Pet é um varejo de produtos e serviços para animais de estimação, com lojas físicas e canais
digitais (e-commerce próprio e marketplace), operando a partir de São Paulo. Ela já tem um módulo que
coleta diariamente os preços de concorrentes e um ERP com custo, margem, estoque e vendas. Mas **a
decisão de preço é manual**: um analista de pricing cruza planilhas e revisa preços em lotes, em datas
fixas (na base, todos os SKUs foram alterados em 01/06, 15/07 e 01/09/2026, cada rodada com um único
motivo genérico).

Isso gera perdas nos dois sentidos: itens acima do mercado perdem volume; itens abaixo deixam margem
na mesa. O desafio pede uma solução que recomende, para cada produto e canal, **SUBIR, BAIXAR, MANTER
ou REVISAR**, com preço sugerido, justificativa e nível de risco, e que permita ao analista **visualizar,
analisar e validar** antes de aplicar. O enunciado é explícito: "o objetivo não é permitir que a IA
altere preços sem controle".

## Indicadores atuais (linha de base) e metas

| Indicador | Hoje | Meta |
|---|---|---|
| Tempo semanal de revisão manual | 18 h | ≤ 6 h |
| SKUs dentro da faixa competitiva | 67% | ≥ 80% |
| Margem bruta média | 31,8% | ≥ 32,5% |
| Taxa de reversão de preços | 7,4% | ≤ 3% |
| Alterações de preço por mês | 146 | monitorar |
| Cobertura de matching confiável | 82% | ≥ 90% |
| Recomendações aceitas pelo time | não medido | ≥ 70% no piloto |
| SKUs monitorados em concorrentes | 1.850 | ≥ 2.000 |

A **métrica primária do piloto é a taxa de aceite ≥ 70%**: recomendações SUBIR/BAIXAR aprovadas como
estão ou editadas com ajuste ≤ 1% do preço atual, sobre todas as SUBIR/BAIXAR com decisão registrada.

## O que o grupo definiu como solução

- Um **fluxo único** roda todo dia após a coleta de concorrência e produz uma recomendação por SKU × canal.
- A **decisão é calculada por modelos matemáticos e regras de negócio** (fora da v1).
- A **IA generativa** entra só na comunicação com o analista: escreve a justificativa e responde perguntas
  (fora da v1; na v1 a justificativa vem pronta do CSV).
- O **analista decide**: aprova, edita, rejeita ou adia cada recomendação; tudo fica registrado.
- Um **painel de métricas visual** mostra a carteira e o efeito das decisões.
- **Objetivo central: agilizar o trabalho do analista** (de 18 h para 6 h por semana).
- Escopo acordado com o mentor: do dado do ERP até a recomendação de decisão. **A aplicação do preço
  nos sistemas de venda fica fora.**

## Regras de negócio da empresa (R01–R12)

Estas regras são aplicadas pelo motor (fora da v1), mas a interface precisa **exibi-las** quando forem
o motivo de uma recomendação REVISAR ou de "exige aprovação".

| ID | Tema | Regra | Ação |
|---|---|---|---|
| R01 | Margem | Preço sugerido nunca pode resultar em margem inferior à margem mínima do SKU/canal | Bloquear |
| R02 | Variação | Alteração máxima de 5% por decisão | Limitar |
| R03 | Curva A | SKU curva A com alteração > 3% exige aprovação humana | Revisar |
| R04 | Estratégicos | Produtos estratégicos nunca são aplicados automaticamente | Revisar |
| R05 | Concorrência | Preço de concorrente indisponível não determina redução automática | Ignorar sinal |
| R06 | Atualidade | Coleta de concorrente com mais de 48 h é desatualizada | Revisar |
| R07 | Canal | Diferença loja física × e-commerce não deve superar 5% sem aprovação | Revisar |
| R08 | Frequência | Mesmo SKU não pode ser alterado mais de uma vez em 3 dias | Bloquear |
| R09 | Promoção | SKU em campanha ativa não pode ser reprecificado automaticamente | Revisar |
| R10 | Anomalia | Variação concorrencial > 20% em 24 h deve ser tratada como anomalia | Revisar |
| R11 | Estoque | Cobertura < 15 dias aumenta risco de redução de preço | Cautela |
| R12 | Excesso | Cobertura > 90 dias + queda por 3 meses sinaliza oportunidade | Priorizar |

## A base de dados (seed/base_popular_pet.xlsx)

Dados fictícios fornecidos no desafio. Cada aba tem 2 linhas de título antes do cabeçalho (`header=2`
no pandas). Abas e conteúdo:

| Aba | Linhas | Colunas principais |
|---|---|---|
| Produtos | 40 | SKU, Produto, Categoria, Marca, Curva ABC, Status, Preço atual, Custo reposição, Margem mínima, Margem alvo, Estoque atual, Cobertura (dias), Venda média/dia |
| Precos_Atuais | 120 | SKU, Canal, Preço atual, Data referência |
| Custos_Margens | 120 | SKU, Canal, Custo reposição, Impostos estimados, Frete rateado, Taxa canal, Margem mínima, Margem alvo, Custo total referência |
| Vendas_12m | 1.440 | Mês (AAAA-MM), SKU, Canal, Quantidade, Receita, Preço médio, Desconto médio |
| Estoque | 40 | SKU, Estoque atual, Cobertura dias, Pedido compra aberto, Previsão recebimento, Local |
| Concorrencia | 120 | SKU, Concorrente, Correspondência, Preço, Disponível, Frete, Data/hora coleta, Confiabilidade matching |
| Historico_Precos | 120 | SKU, Data, Preço, Motivo, Origem |
| Promocoes | 8 | SKU, Campanha, Início, Fim, Desconto, Regra |
| Regras_Negocio | 12 | ID, Tema, Regra fictícia, Ação esperada, Criticidade |
| Indicadores_Atuais | 8 | Indicador, Valor fictício atual, Meta fictícia, Frequência, Responsável |
| Dicionario_Dados | 11 | Aba, Campo, Tipo, Definição, Origem, Periodicidade, Sensível? |

Observações: 3 canais fixos ("Loja física", "E-commerce", "Marketplace"); 2 SKUs com status
"Descontinuando" (PP-0037, PP-0040); 8 SKUs em campanha de 05 a 12/09/2026; datas em `dd/mm/aaaa`;
valores absolutos irreais (ex.: ração de 10 kg a R$ 4,38), então a interface sempre mostra também
percentuais.

## O arquivo de recomendações (seed/recomendacoes_rodada_2026-09-09.csv)

Saída de uma rodada do motor para 40 SKUs × 3 canais = 120 linhas. Uma linha por SKU × canal, já
ordenada por prioridade. Distribuição: 38 BAIXAR, 20 SUBIR, 16 MANTER, 46 REVISAR. Colunas:

| Coluna | Tipo | Significado |
|---|---|---|
| prioridade | int | posição na lista (1 = maior valor em jogo) |
| sku, produto, categoria, curva_abc, canal | texto | identificação |
| preco_atual, preco_mercado, menor_concorrente, custo | decimal (R$) | preços e custo de reposição |
| margem_atual, margem_minima, margem_alvo, margem_liquida | decimal (0–1) | margens; `margem_liquida` desconta impostos, frete e taxa do canal |
| estoque | int | unidades |
| cobertura_dias | decimal | dias de estoque ao ritmo recente |
| tendencia_mes | decimal | variação mensal das vendas (ex.: −0,03 = −3%/mês) |
| var_12m | decimal | variação das vendas em 12 meses |
| recomendacao | enum | SUBIR, BAIXAR, MANTER, REVISAR |
| preco_sugerido | decimal (R$) | igual ao atual quando MANTER |
| variacao | decimal | preco_sugerido / preco_atual − 1 |
| margem_resultante | decimal | margem com o preço sugerido |
| nivel_risco | enum | Baixo, Médio, Alto |
| risco_score | decimal | 0–100 |
| confianca_dados | decimal (0–1) | confiança nos dados de concorrência |
| exige_aprovacao | bool | precisa de validação de gestor |
| receita_mensal_est | decimal (R$) | receita mensal estimada do SKU no canal |
| impacto_mensal_est | decimal (R$) | variação de margem mensal estimada (pode ser negativa; é estimativa) |
| justificativa | texto | explicação pronta, em português |
| motivos_revisao | texto | motivos separados por "; " (vazio quando não há) |
| alertas_dados | texto | alertas de qualidade de dados separados por "; " (vazio quando não há) |
| rodada_data | data | data da rodada (2026-09-09) |
