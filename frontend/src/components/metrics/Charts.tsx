import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DecisionBucket, RecommendationType, RoundMetrics } from '../../api/types'
import { formatNumber } from '../../lib/format'
import { EmptyState } from '../States'
import {
  AXIS_TICK,
  BRAND,
  BUCKET_FILL,
  BUCKET_LABEL,
  BUCKET_STROKE,
  RECOMMENDATION_FILL,
  RECOMMENDATION_STROKE,
} from './chartColors'
import { ChartTooltip } from './ChartCard'

const RECS: RecommendationType[] = ['SUBIR', 'BAIXAR', 'MANTER', 'REVISAR']
const BUCKETS: DecisionBucket[] = [
  'APROVADA',
  'EDITADA',
  'REJEITADA',
  'ADIADA',
  'PENDENTE',
  'SEM_ACAO',
]
const HOVER_CURSOR = { fill: '#F1ECF7' }

export function DistributionChart({ data }: { data: RoundMetrics['recommendation_distribution'] }) {
  const rows = RECS.map((rec) => ({ name: rec, value: data[rec] }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 40 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke={BRAND.line} />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ ...AXIS_TICK, fill: BRAND.ink, fontWeight: 700 }}
          width={72}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={HOVER_CURSOR}
          content={({ active, payload }) => (
            <ChartTooltip
              active={active}
              label={payload?.[0]?.payload.name}
              rows={payload?.length ? [{ name: 'Itens', value: String(payload[0].value) }] : []}
            />
          )}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {rows.map((r) => (
            <Cell
              key={r.name}
              fill={RECOMMENDATION_FILL[r.name]}
              stroke={RECOMMENDATION_STROKE[r.name]}
            />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            fill={BRAND.ink}
            stroke="none"
            fontSize={12}
            fontWeight={700}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PriceIndexChart({ data }: { data: RoundMetrics['price_index_by_curve'] }) {
  const rows = (['A', 'B', 'C'] as const)
    .filter((c) => data[c] !== null)
    .map((c) => ({
      name: `Curva ${c}`,
      value: data[c] as number,
      delta: (data[c] as number) - 100,
    }))
  if (!rows.length) return <EmptyState title="Sem dados de mercado para os filtros" />
  // Barras partem da referência 100: acima = mais caro que o mercado; abaixo = mais barato.
  const spread = Math.max(2, ...rows.map((r) => Math.ceil(Math.abs(r.delta) + 0.5)))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} margin={{ top: 16, right: 96 }} barCategoryGap="30%">
        <CartesianGrid vertical={false} stroke={BRAND.line} />
        <XAxis
          dataKey="name"
          tick={{ ...AXIS_TICK, fill: BRAND.ink }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[-spread, spread]}
          tickFormatter={(v: number) => String(100 + v)}
          tick={AXIS_TICK}
          width={40}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          cursor={HOVER_CURSOR}
          content={({ active, payload }) => (
            <ChartTooltip
              active={active}
              label={payload?.[0]?.payload.name}
              rows={
                payload?.length
                  ? [{ name: 'Índice de preço', value: formatNumber(payload[0].payload.value) }]
                  : []
              }
            />
          )}
        />
        <ReferenceLine
          y={0}
          stroke={BRAND.lime}
          strokeWidth={2}
          label={{
            value: 'mercado = 100',
            position: 'insideTopRight',
            fill: BRAND.limeData,
            fontSize: 11,
            fontWeight: 700,
          }}
        />
        <Bar
          dataKey="delta"
          fill={BRAND.purpleData}
          radius={4}
          maxBarSize={56}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="value"
            position="top"
            fill={BRAND.ink}
            stroke="none"
            fontSize={12}
            fontWeight={700}
            formatter={(v: number) => formatNumber(v)}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function DecisionsChart({ data }: { data: RoundMetrics['decisions_by_recommendation'] }) {
  const rows = RECS.map((rec) => ({ name: rec, ...data[rec] }))
  const present = BUCKETS.filter((b) => rows.some((r) => r[b] > 0))
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke={BRAND.line} />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ ...AXIS_TICK, fill: BRAND.ink, fontWeight: 700 }}
          width={72}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={HOVER_CURSOR}
          content={({ active, payload, label }) => (
            <ChartTooltip
              active={active}
              label={label as string}
              rows={(payload ?? [])
                .filter((p) => (p.value as number) > 0)
                .map((p) => ({
                  name: BUCKET_LABEL[p.dataKey as DecisionBucket],
                  value: String(p.value),
                  color: BUCKET_FILL[p.dataKey as DecisionBucket],
                }))}
            />
          )}
        />
        <Legend
          content={() => (
            <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1 pt-2 text-xs text-ink">
              {present.map((b) => (
                <li key={b} className="flex items-center gap-1.5">
                  <span
                    className="inline-block h-3 w-3 rounded-sm border"
                    style={{ background: BUCKET_FILL[b], borderColor: BUCKET_STROKE[b] }}
                  />
                  {BUCKET_LABEL[b]}
                </li>
              ))}
            </ul>
          )}
        />
        {present.map((bucket) => (
          <Bar
            key={bucket}
            dataKey={bucket}
            stackId="decisions"
            fill={BUCKET_FILL[bucket]}
            stroke={BUCKET_STROKE[bucket]}
            isAnimationActive={false}
          >
            <LabelList
              dataKey={bucket}
              position="center"
              fill={BRAND.ink}
              stroke="none"
              fontSize={11}
              fontWeight={700}
              formatter={(v: number) => (v >= 3 ? v : '')}
            />
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

export function RejectionReasonsChart({ data }: { data: RoundMetrics['rejection_reasons'] }) {
  const rows = Object.entries(data).map(([name, value]) => ({ name, value }))
  if (rows.every((r) => r.value === 0))
    return (
      <EmptyState title="Nenhuma rejeição registrada">
        Os motivos aparecem aqui quando o analista rejeitar recomendações.
      </EmptyState>
    )
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 40 }} barCategoryGap={8}>
        <CartesianGrid horizontal={false} stroke={BRAND.line} />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ ...AXIS_TICK, fill: BRAND.ink }}
          width={200}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={HOVER_CURSOR}
          content={({ active, payload }) => (
            <ChartTooltip
              active={active}
              label={payload?.[0]?.payload.name}
              rows={payload?.length ? [{ name: 'Rejeições', value: String(payload[0].value) }] : []}
            />
          )}
        />
        <Bar
          dataKey="value"
          fill={BRAND.purpleData}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="value"
            position="right"
            fill={BRAND.ink}
            stroke="none"
            fontSize={12}
            fontWeight={700}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
