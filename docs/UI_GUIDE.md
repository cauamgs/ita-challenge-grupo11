# Guia de UI — identidade Popular Pet

A interface segue a identidade já usada nos documentos do grupo: roxo da marca como cor principal,
verde-lima como acento, muito branco, tipografia limpa. Referência visual: `assets/logo_popular_pet.png`
(logo com fundo roxo, símbolo de pata em verde-lima, slogan "Quem ama Cuida").

## 1. Tokens (Tailwind `theme.extend`)

```js
colors: {
  brand: {
    purple:      '#5E3A85',  // principal: cabeçalhos, botões primários, títulos
    purpleDark:  '#3F2460',  // hover de botão primário, capa
    purpleData:  '#7B4FA8',  // barras e linhas de gráfico (validado para contraste)
    purpleLight: '#F1ECF7',  // fundos de painel, linhas alternadas, cards
    purpleLine:  '#D9CEE8',  // bordas
    lime:        '#B4C805',  // acento: faixa de destaque, botão de ação secundária, marcador de meta
    limeText:    '#7E9A0A',  // texto sobre fundo claro (o lime puro não tem contraste para texto)
    limeLight:   '#F3F7D9',  // fundo de resumo/caixas de destaque
    limeData:    '#7E9A0A',  // segunda série de gráfico
  },
  ink:   { DEFAULT: '#222222', muted: '#666666', faint: '#999999' },
  line:  '#E5E0EC',
  surface: '#FFFFFF',
  tag: {
    baixar: '#FDE2E1', subir: '#DCEFD9', manter: '#EEEEEE', revisar: '#FFF2CC',
    riscoBaixo: '#DCEFD9', riscoMedio: '#FFF2CC', riscoAlto: '#FDE2E1',
  },
}
fontFamily: { sans: ['Inter', 'DejaVu Sans', 'Arial', 'sans-serif'] }
borderRadius: { card: '6px' }
```

Regras de cor:
- Texto de tags e rótulos sempre em `ink` (nunca colorido); a cor fica no fundo da tag.
- Gráficos usam `purpleData` como série principal e `limeData` como secundária; nunca mais de duas
  séries sem legenda; sem eixo duplo.
- `lime` puro só em fundos, barras e marcadores; texto sobre claro usa `limeText`.

## 2. Tipografia e espaçamento

- Fonte Inter (carregar via `@fontsource/inter` para não depender de rede em produção).
- Título de página: 22px/700 roxo. Título de seção: 15px/700 roxo. Rótulo de seção pequeno (kicker):
  10px/700 caixa alta, espaçamento 1.5px, `limeText`.
- Corpo: 14px/400 `ink`. Texto auxiliar: 12px `ink.muted`.
- Espaçamento base 4px; padding de cards 12–16px; gap entre cards 12px.

## 3. Componentes

### AppShell
- Barra superior roxa (`brand.purple`), 56px, com logo (altura 32px, cantos arredondados), título da
  área em branco e, à direita, seletor de rodada e seletor de analista (fundo branco translúcido).
- Navegação por abas abaixo da barra: Recomendações · Métricas · Histórico. Aba ativa com borda
  inferior `lime` 3px e texto roxo.
- Faixa fina `lime` (4px) no rodapé das páginas.

### Tag
- Pílula 20px de altura, raio 10px, texto 11px/700 `ink`, fundo conforme mapa `tag.*`.
- Recomendação: BAIXAR (rosa), SUBIR (verde), MANTER (cinza), REVISAR (amarelo).
- Risco: Baixo (verde), Médio (amarelo), Alto (rosa).
- Decisão: Pendente (contorno cinza, sem fundo), Aprovada (verde), Editada (amarelo), Rejeitada (rosa),
  Adiada (cinza).

### Botões
- Primário: fundo roxo, texto branco, hover `purpleDark`.
- Ação positiva (Aprovar): fundo `tag.subir`, texto `ink`, borda `#B9DDB0`.
- Ação neutra (Editar/Adiar): fundo `tag.revisar` / `tag.manter`.
- Ação negativa (Rejeitar): fundo `tag.baixar`, borda `#F0B8B5`.
- Secundário: fundo `lime`, texto `purpleDark`, 700 (ex.: "Exportar aprovadas").
- Altura 32px, raio 4px, padding 0 12px.

### Card de métrica (KPI)
- Fundo branco, borda `line`, borda superior 4px roxa, raio 6px, padding 12px.
- Valor 26px/800 roxo; rótulo 12px `ink.muted`; meta 12px/700 `limeText` (ex.: "meta ≥ 70%").
- Quando o valor atinge a meta, o valor fica `limeText`; quando não, permanece roxo. Nunca vermelho.

### Caixa de destaque
- `limeLight` com borda esquerda 4px `lime` (resumo da rodada, avisos positivos).
- `purpleLight` com borda esquerda 4px roxa (notas, informações).

### Tabela
- Cabeçalho roxo com texto branco 12px/600; linhas 13px; zebra com `#FAF8FC`; linha decidida com fundo
  `#F4F4F4`; hover `purpleLight`; célula numérica alinhada à direita, fonte tabular.
- Cabeçalho fixo ao rolar.

### Drawer de detalhe
- Largura 520px, fundo branco, sombra suave, fecha com Esc e clique fora.
- Cabeçalho com SKU · Produto · Canal e tags; blocos separados por título de seção pequeno.
- Grade de números em duas colunas, rótulo `ink.muted` 12px acima do valor 14px.

### Filtros
- Selects e inputs com fundo `purpleLight`, borda `purpleLine`, altura 32px, raio 4px, 13px.

## 4. Layout das telas (referência)

### Recomendações
```
┌ AppShell (barra roxa: logo · "Recomendações de preço" · rodada ▾ · analista ▾) ┐
│ Abas: [Recomendações] Métricas Histórico                                        │
│ ┌ caixa lime: Resumo da rodada: 120 itens · 58 alterações · 46 revisar … ┐      │
│ [Canal▾][Curva▾][Recomendação▾][Risco▾][Status▾][☐ Só exige aprovação][busca] [Exportar aprovadas] │
│ ┌ tabela ─────────────────────────────────────────────────────────────────┐    │
│ │ # │ SKU · Produto │ Canal │ Atual │ Mercado │ Rec. │ Sugerido │ Var. │ Margem │ Risco │ Valor em jogo │ Aprov. │ Decisão │
│ └───────────────────────────────────────────────────────────────────────────┘    │
│                                              ┌ Drawer: detalhe do item ─────┐   │
│                                              │ Justificativa · Números ·     │   │
│                                              │ Motivos · Alertas · Decisão   │   │
└──────────────────────────────────────────────┴───────────────────────────────┘───┘
```

### Métricas
```
│ [Rodada▾][Canal▾][Curva▾]                                                       │
│ [Aceite 72% ≥70%] [Tempo est. 5,5h ≤6h] [Na faixa 78% ≥80%] [Margem 32,3% ≥32,5%] [Reversão — ≤3%] │
│ ┌ Distribuição das recomendações ┐ ┌ Índice de preço por curva (ref. 100) ┐      │
│ ┌ Decisões por recomendação ─────┐ ┌ Motivos de rejeição ───────────────┐        │
│ ┌ Top 10 por valor em jogo (tabela) ─────────────────────────────────────┐        │
```

## 5. Formatação

- `formatBRL(1234.5) → "R$ 1.234,50"`; `formatPct(0.023, {sign:true}) → "+2,3%"`;
  `formatDate("2026-09-09") → "09/09/2026"`. Centralize em `src/lib/format.ts`.
- Números em tabelas com `font-variant-numeric: tabular-nums`.

## 6. Tom dos textos

Português do Brasil, direto, sem jargão técnico. Exemplos: "Nenhuma decisão registrada nesta rodada",
"Preço abaixo do piso de margem mínima (R$ 96,50). Confirme antes de aplicar.", "Exige aprovação de
gestor: curva A com variação acima de 3%".
