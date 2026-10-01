/** Regras de negócio R01–R12 (CONTEXTO_DESAFIO.md), exibidas quando citadas nos motivos. */
export const BUSINESS_RULES: Record<string, { theme: string; rule: string }> = {
  R01: {
    theme: 'Margem',
    rule: 'Preço sugerido nunca pode resultar em margem inferior à mínima do SKU/canal',
  },
  R02: { theme: 'Variação', rule: 'Alteração máxima de 5% por decisão' },
  R03: { theme: 'Curva A', rule: 'SKU curva A com alteração > 3% exige aprovação humana' },
  R04: { theme: 'Estratégicos', rule: 'Produtos estratégicos nunca são aplicados automaticamente' },
  R05: {
    theme: 'Concorrência',
    rule: 'Preço de concorrente indisponível não determina redução automática',
  },
  R06: { theme: 'Atualidade', rule: 'Coleta de concorrente com mais de 48 h é desatualizada' },
  R07: {
    theme: 'Canal',
    rule: 'Diferença loja física × e-commerce não deve superar 5% sem aprovação',
  },
  R08: { theme: 'Frequência', rule: 'Mesmo SKU não pode ser alterado mais de uma vez em 3 dias' },
  R09: {
    theme: 'Promoção',
    rule: 'SKU em campanha ativa não pode ser reprecificado automaticamente',
  },
  R10: {
    theme: 'Anomalia',
    rule: 'Variação concorrencial > 20% em 24 h deve ser tratada como anomalia',
  },
  R11: { theme: 'Estoque', rule: 'Cobertura < 15 dias aumenta risco de redução de preço' },
  R12: { theme: 'Excesso', rule: 'Cobertura > 90 dias + queda por 3 meses sinaliza oportunidade' },
}

export function rulesIn(texts: string[]): string[] {
  const found = new Set<string>()
  for (const text of texts) for (const m of text.matchAll(/\bR(0[1-9]|1[0-2])\b/g)) found.add(m[0])
  return [...found].sort()
}
