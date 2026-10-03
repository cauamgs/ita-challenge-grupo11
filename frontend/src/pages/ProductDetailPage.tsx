import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useProduct } from '../api/platform'
import type { Channel, PriceChangeType } from '../api/types'
import { buttonClass } from '../components/Button'
import { Breadcrumb, Card, PageHeader } from '../components/Card'
import { PriceEvolutionChart } from '../components/charts/PlatformCharts'
import { EmptyState, ErrorBox, Loading } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { PriceChangeTag, RecommendationTag, RiskTag, StatusTag } from '../components/Tag'
import {
  formatBRL,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPct,
  plural,
} from '../lib/format'
import { CHANNEL_LABEL, DECISION_LABEL, PRICE_SOURCE_LABEL } from '../lib/labels'

const CHANNELS: Channel[] = ['LOJA_FISICA', 'ECOMMERCE', 'MARKETPLACE']

export function ProductDetailPage() {
  const { sku = '' } = useParams()
  const { data: p, isLoading, error } = useProduct(sku)
  const [channel, setChannel] = useState<Channel | ''>('')
  const [kind, setKind] = useState<PriceChangeType | ''>('')

  if (isLoading) return <Loading />
  if (error || !p) return <ErrorBox error={error} />

  const changes = p.price_history.filter((e) => e.change_type !== 'INICIAL')
  const ups = changes.filter((e) => e.change_type === 'AUMENTO').length
  const events = p.price_history.filter(
    (e) => (!channel || e.channel === channel) && (!kind || e.change_type === kind),
  )

  return (
    <div className="space-y-4">
      <Breadcrumb items={[{ label: 'Produtos', to: '/produtos' }, { label: p.sku }]} />
      <PageHeader
        kicker={`${p.category} · ${p.brand}`}
        title={`${p.sku} · ${p.name}`}
        description={
          <>
            Curva <strong>{p.abc_curve}</strong> · status <strong>{p.status}</strong>
            {p.is_strategic && ' · produto estratégico'} ·{' '}
            {plural(changes.length, 'alteração', 'alterações')} de preço (
            {plural(ups, 'aumento', 'aumentos')},{' '}
            {plural(changes.length - ups, 'redução', 'reduções')})
          </>
        }
        actions={
          <Link to={`/recomendacoes?q=${p.sku}`} className={buttonClass('primary')}>
            Ver recomendações do SKU
          </Link>
        }
      />

      <div className="grid gap-3 md:grid-cols-3">
        {CHANNELS.map((c) => {
          const s = p.channels.find((x) => x.channel === c)
          if (!s) return null
          return (
            <Card key={c} className="border-t-4 border-t-brand-purple">
              <p className="text-xs font-semibold text-ink-muted">{CHANNEL_LABEL[c]}</p>
              <p className="tabular text-[26px] font-extrabold leading-tight text-brand-purple">
                {formatBRL(s.current_price)}
              </p>
              <p className="text-xs text-ink-muted">
                preço vigente em {formatDate(s.reference_date)}
              </p>
              <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                <dt className="text-ink-muted">Custo de reposição</dt>
                <dd className="tabular text-right">{formatBRL(s.replacement_cost)}</dd>
                <dt className="text-ink-muted">Piso de margem</dt>
                <dd className="tabular text-right">{formatBRL(s.min_price_floor)}</dd>
                <dt className="text-ink-muted">Margem mín. / alvo</dt>
                <dd className="tabular text-right">
                  {formatPct(s.min_margin)} / {formatPct(s.target_margin)}
                </dd>
                <dt className="text-ink-muted">Taxa do canal</dt>
                <dd className="tabular text-right">{formatPct(s.channel_fee)}</dd>
              </dl>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-3 lg:grid-cols-[3fr_1fr]">
        <Card
          title="Evolução do preço"
          subtitle="Por canal; cada degrau é uma alteração registrada no ERP"
        >
          {p.price_history.length ? (
            <PriceEvolutionChart events={p.price_history} current={p.channels} />
          ) : (
            <EmptyState title="Sem histórico de preço" />
          )}
        </Card>
        <Card title="Estoque">
          {p.stock ? (
            <dl className="space-y-2 text-[13px]">
              <div>
                <dt className="text-xs text-ink-muted">Em estoque</dt>
                <dd className="tabular text-[22px] font-extrabold text-brand-purple">
                  {p.stock.quantity} un.
                </dd>
              </div>
              <div>
                <dt className="text-xs text-ink-muted">Cobertura</dt>
                <dd className="tabular">{formatNumber(p.stock.coverage_days)} dias</dd>
              </div>
              <div>
                <dt className="text-xs text-ink-muted">Pedido de compra aberto</dt>
                <dd className="tabular">
                  {p.stock.open_po_quantity} un.
                  {p.stock.expected_receipt &&
                    ` · previsto ${formatDate(p.stock.expected_receipt)}`}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-ink-muted">Local</dt>
                <dd>{p.stock.location ?? '—'}</dd>
              </div>
            </dl>
          ) : (
            <EmptyState title="Sem estoque informado" />
          )}
        </Card>
      </div>

      <Card
        title="Histórico de alterações de preço"
        subtitle="Aumentos, reduções e o primeiro preço conhecido em cada canal, do mais recente ao mais antigo"
        action={
          <div className="flex gap-2">
            <select
              aria-label="Filtrar por canal"
              className="h-8 rounded border border-brand-purpleLine bg-brand-purpleLight px-2 text-[13px]"
              value={channel}
              onChange={(e) => setChannel(e.target.value as Channel | '')}
            >
              <option value="">Todos os canais</option>
              {CHANNELS.map((c) => (
                <option key={c} value={c}>
                  {CHANNEL_LABEL[c]}
                </option>
              ))}
            </select>
            <select
              aria-label="Filtrar por tipo"
              className="h-8 rounded border border-brand-purpleLine bg-brand-purpleLight px-2 text-[13px]"
              value={kind}
              onChange={(e) => setKind(e.target.value as PriceChangeType | '')}
            >
              <option value="">Todos os tipos</option>
              <option value="AUMENTO">Aumentos</option>
              <option value="REDUCAO">Reduções</option>
              <option value="INICIAL">Registro inicial</option>
            </select>
          </div>
        }
      >
        <TableContainer>
          <thead>
            <tr>
              <Th>Data</Th>
              <Th>Canal</Th>
              <Th>Alteração</Th>
              <Th numeric>De</Th>
              <Th numeric>Para</Th>
              <Th>Motivo</Th>
              <Th>Origem</Th>
              <Th>Fonte</Th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 && (
              <tr>
                <td colSpan={8}>
                  <EmptyState title="Nenhuma alteração para os filtros" />
                </td>
              </tr>
            )}
            {events.map((e, i) => (
              <tr key={e.id} className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}>
                <Td className="tabular whitespace-nowrap">{formatDate(e.effective_date)}</Td>
                <Td className="whitespace-nowrap">{CHANNEL_LABEL[e.channel]}</Td>
                <Td>
                  <PriceChangeTag value={e.change_type} variation={e.variation} />
                </Td>
                <Td numeric>{formatBRL(e.old_price)}</Td>
                <Td numeric className="font-semibold">
                  {formatBRL(e.new_price)}
                </Td>
                <Td>{e.reason ?? '—'}</Td>
                <Td>{e.origin ?? '—'}</Td>
                <Td
                  className="whitespace-nowrap text-xs text-ink-muted"
                  title={`Registrado em ${formatDateTime(e.recorded_at)}`}
                >
                  {PRICE_SOURCE_LABEL[e.source]}
                </Td>
              </tr>
            ))}
          </tbody>
        </TableContainer>
      </Card>

      <Card title="Recomendações e decisões" subtitle="Todas as rodadas em que o SKU apareceu">
        {p.recommendations.length === 0 ? (
          <EmptyState title="O SKU ainda não apareceu em nenhuma rodada" />
        ) : (
          <TableContainer>
            <thead>
              <tr>
                <Th>Rodada</Th>
                <Th>Canal</Th>
                <Th>Recomendação</Th>
                <Th numeric>Atual</Th>
                <Th numeric>Sugerido</Th>
                <Th numeric>Variação</Th>
                <Th>Risco</Th>
                <Th>Decisão</Th>
                <Th>Por</Th>
              </tr>
            </thead>
            <tbody>
              {p.recommendations.map((r, i) => (
                <tr key={r.id} className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}>
                  <Td className="tabular">{formatDate(r.round_date)}</Td>
                  <Td>{CHANNEL_LABEL[r.channel]}</Td>
                  <Td>
                    <RecommendationTag value={r.recommendation} />
                  </Td>
                  <Td numeric>{formatBRL(r.current_price)}</Td>
                  <Td numeric>{formatBRL(r.suggested_price)}</Td>
                  <Td numeric>{formatPct(r.variation, { sign: true })}</Td>
                  <Td>
                    <RiskTag value={r.risk_level} />
                  </Td>
                  <Td>
                    <Link
                      to={`/recomendacoes?item=${r.id}`}
                      className="inline-flex"
                      title="Abrir a recomendação"
                    >
                      <StatusTag value={r.status} />
                    </Link>
                  </Td>
                  <Td className="text-xs text-ink-muted">
                    {r.last_decision
                      ? `${DECISION_LABEL[r.last_decision.decision]} por ${r.last_decision.user_name} em ${formatDateTime(r.last_decision.created_at)}`
                      : '—'}
                  </Td>
                </tr>
              ))}
            </tbody>
          </TableContainer>
        )}
      </Card>
    </div>
  )
}
