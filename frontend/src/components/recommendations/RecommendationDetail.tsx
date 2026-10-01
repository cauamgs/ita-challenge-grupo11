import type { ReactNode } from 'react'
import { useRecommendation } from '../../api/queries'
import type { RecommendationDetail as Detail } from '../../api/types'
import { formatBRL, formatNumber, formatPct } from '../../lib/format'
import { CHANNEL_LABEL } from '../../lib/labels'
import { BUSINESS_RULES, rulesIn } from '../../lib/rules'
import { SectionTitle } from '../Drawer'
import { ApprovalIcon } from '../Icons'
import { ErrorBox, Loading } from '../States'
import { RecommendationTag, RiskTag, StatusTag } from '../Tag'

function NumberCell({ label, value, note }: { label: string; value: ReactNode; note?: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-muted">
        {label}
        {note && <span className="ml-1 text-[11px] italic text-ink-faint">({note})</span>}
      </dt>
      <dd className="tabular text-sm">{value}</dd>
    </div>
  )
}

function Numbers({ d }: { d: Detail }) {
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
      <NumberCell label="Preço atual" value={formatBRL(d.current_price)} />
      <NumberCell label="Preço de mercado" value={formatBRL(d.market_price)} />
      <NumberCell label="Menor concorrente válido" value={formatBRL(d.lowest_valid_competitor)} />
      <NumberCell label="Preço sugerido" value={<strong>{formatBRL(d.suggested_price)}</strong>} />
      <NumberCell label="Variação" value={formatPct(d.variation, { sign: true })} />
      <NumberCell label="Custo de reposição" value={formatBRL(d.cost)} />
      <NumberCell label="Margem atual" value={formatPct(d.current_margin)} />
      <NumberCell label="Margem mínima" value={formatPct(d.min_margin)} />
      <NumberCell label="Margem alvo" value={formatPct(d.target_margin)} />
      <NumberCell label="Margem resultante" value={formatPct(d.resulting_margin)} />
      <NumberCell label="Margem líquida do canal" value={formatPct(d.net_margin)} />
      <NumberCell label="Estoque" value={`${formatNumber(d.stock_qty, 0)} un.`} />
      <NumberCell label="Cobertura" value={`${formatNumber(d.coverage_days)} dias`} />
      <NumberCell
        label="Tendência de vendas"
        value={`${formatPct(d.sales_trend_month, { sign: true })}/mês`}
      />
      <NumberCell
        label="Variação de vendas 12 m"
        value={formatPct(d.sales_var_12m, { sign: true })}
      />
      <NumberCell label="Confiança dos dados" value={formatPct(d.data_confidence)} />
      <NumberCell
        label="Receita mensal"
        value={formatBRL(d.est_monthly_revenue)}
        note="estimativa"
      />
      <NumberCell
        label="Impacto mensal"
        value={formatBRL(d.est_monthly_impact)}
        note="estimativa"
      />
      <NumberCell label="Piso de margem mínima" value={formatBRL(d.min_price_floor)} />
      <NumberCell
        label="Valor em jogo"
        value={d.value_at_stake === null ? '—' : `${formatBRL(d.value_at_stake)}/mês`}
      />
    </dl>
  )
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

function RuleChips({ codes }: { codes: string[] }) {
  if (!codes.length) return null
  return (
    <ul className="mt-2 space-y-1">
      {codes.map((code) => (
        <li key={code} className="text-xs text-ink-muted">
          <span className="mr-1.5 rounded bg-brand-purpleLight px-1.5 py-0.5 font-bold text-brand-purple">
            {code}
          </span>
          {BUSINESS_RULES[code].theme}: {BUSINESS_RULES[code].rule}
        </li>
      ))}
    </ul>
  )
}

export function RecommendationDetailView({
  id,
  decisionSlot,
}: {
  id: string
  decisionSlot?: (detail: Detail) => ReactNode
}) {
  const { data: d, isLoading, error } = useRecommendation(id)

  if (isLoading)
    return (
      <div className="p-5">
        <Loading label="Carregando detalhe…" />
      </div>
    )
  if (error || !d)
    return (
      <div className="p-5">
        <ErrorBox error={error} />
      </div>
    )

  const rules = rulesIn([...d.review_reasons, ...d.data_alerts])

  return (
    <div>
      <header className="border-b border-line bg-brand-purpleLight px-5 pb-3 pt-4 pr-12">
        <p className="text-xs font-semibold text-brand-purple">
          #{d.priority} · Curva {d.abc_curve} · {d.category}
        </p>
        <h2 className="mt-0.5 text-[17px] font-bold leading-snug text-brand-purple">
          {d.sku} · {d.product_name} · {CHANNEL_LABEL[d.channel]}
        </h2>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <RecommendationTag value={d.recommendation} />
          <RiskTag value={d.risk_level} />
          <StatusTag value={d.status} />
          {d.product.status !== 'Ativo' && (
            <span className="text-xs text-ink-muted">Produto: {d.product.status}</span>
          )}
        </div>
      </header>

      <div className="space-y-5 px-5 py-4">
        <section>
          <SectionTitle>Justificativa</SectionTitle>
          <p className="text-sm leading-relaxed">{d.justification}</p>
        </section>

        <section>
          <SectionTitle>Números</SectionTitle>
          <Numbers d={d} />
        </section>

        {d.review_reasons.length > 0 && (
          <section>
            <SectionTitle>Motivos de revisão</SectionTitle>
            <BulletList items={d.review_reasons} />
          </section>
        )}

        {d.data_alerts.length > 0 && (
          <section>
            <SectionTitle>Alertas de dados</SectionTitle>
            <BulletList items={d.data_alerts} />
          </section>
        )}

        {(d.requires_approval || rules.length > 0) && (
          <section>
            <SectionTitle>Regras</SectionTitle>
            {d.requires_approval && (
              <div className="flex items-start gap-2 rounded-card border-l-4 border-brand-purple bg-brand-purpleLight px-3 py-2 text-sm">
                <ApprovalIcon className="mt-0.5 h-4 w-4 shrink-0" />
                <strong>Exige aprovação de gestor</strong>
              </div>
            )}
            <RuleChips codes={rules} />
          </section>
        )}

        {decisionSlot?.(d)}
      </div>
    </div>
  )
}
