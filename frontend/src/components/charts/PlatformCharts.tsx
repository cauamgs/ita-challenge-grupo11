import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Channel, DayCount, PriceEvent } from '../../api/types'
import { formatBRL, formatDate, formatDayMonth, formatMonth } from '../../lib/format'
import { CHANNEL_LABEL } from '../../lib/labels'
import { ChartTooltip } from '../metrics/ChartCard'
import { AXIS_TICK, BRAND } from '../metrics/chartColors'

const CURSOR = { fill: '#F1ECF7' }

/** Decisões registradas por dia (série única: o título do cartão nomeia a série). */
export function DecisionsByDayChart({ data, height = 180 }: { data: DayCount[]; height?: number }) {
  const rows = data.map((d) => ({ ...d, label: formatDayMonth(d.date) }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -18 }}>
        <CartesianGrid vertical={false} stroke={BRAND.line} />
        <XAxis
          dataKey="label"
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
          minTickGap={12}
        />
        <YAxis allowDecimals={false} tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={CURSOR}
          content={({ active, payload }) => (
            <ChartTooltip
              active={active}
              label={payload?.[0] ? formatDate(payload[0].payload.date) : undefined}
              rows={payload?.length ? [{ name: 'Decisões', value: String(payload[0].value) }] : []}
            />
          )}
        />
        <Bar
          dataKey="count"
          fill={BRAND.purpleData}
          radius={[4, 4, 0, 0]}
          maxBarSize={28}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Aumentos × reduções de preço por mês (duas séries: legenda + tooltip). */
export function PriceChangesChart({
  data,
}: {
  data: { month: string; increases: number; decreases: number }[]
}) {
  const rows = data.map((d) => ({ ...d, label: formatMonth(d.month) }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -18 }} barGap={2}>
        <CartesianGrid vertical={false} stroke={BRAND.line} />
        <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <YAxis allowDecimals={false} tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={CURSOR}
          content={({ active, payload, label }) => (
            <ChartTooltip
              active={active}
              label={label as string}
              rows={(payload ?? []).map((p) => ({
                name: p.dataKey === 'increases' ? 'Aumentos' : 'Reduções',
                value: String(p.value),
                color: p.dataKey === 'increases' ? BRAND.purpleData : BRAND.limeData,
              }))}
            />
          )}
        />
        <Legend
          content={() => (
            <ul className="flex justify-center gap-4 pt-1 text-xs text-ink">
              <li className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm" style={{ background: BRAND.purpleData }} />
                Aumentos
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm" style={{ background: BRAND.limeData }} />
                Reduções
              </li>
            </ul>
          )}
        />
        <Bar
          dataKey="increases"
          fill={BRAND.purpleData}
          radius={[4, 4, 0, 0]}
          maxBarSize={22}
          isAnimationActive={false}
        />
        <Bar
          dataKey="decreases"
          fill={BRAND.limeData}
          radius={[4, 4, 0, 0]}
          maxBarSize={22}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

const CHANNEL_STYLE: Record<Channel, { color: string; dash?: string }> = {
  LOJA_FISICA: { color: BRAND.purpleData },
  ECOMMERCE: { color: BRAND.limeData },
  MARKETPLACE: { color: '#8A8A8A', dash: '5 4' },
}
const CHANNELS: Channel[] = ['LOJA_FISICA', 'ECOMMERCE', 'MARKETPLACE']

/** Evolução do preço por canal (linha em degraus: o preço vale até a próxima alteração). */
export function PriceEvolutionChart({
  events,
  current,
}: {
  events: PriceEvent[]
  current: { channel: Channel; current_price: number; reference_date: string }[]
}) {
  const channels = CHANNELS.filter(
    (c) => events.some((e) => e.channel === c) || current.some((s) => s.channel === c),
  )
  const dates = [
    ...new Set([...events.map((e) => e.effective_date), ...current.map((c) => c.reference_date)]),
  ].sort()
  const rows = dates.map((date) => {
    const row: Record<string, string | number | null> = { date, label: formatDate(date) }
    for (const channel of channels) {
      const known = events
        .filter((e) => e.channel === channel && e.effective_date <= date)
        .sort((a, b) => a.effective_date.localeCompare(b.effective_date))
      row[channel] = known.length ? known[known.length - 1].new_price : null
    }
    return row
  })
  return (
    <ResponsiveContainer width="100%" height={230}>
      <LineChart data={rows} margin={{ top: 10, right: 16, left: 4 }}>
        <CartesianGrid vertical={false} stroke={BRAND.line} />
        <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <YAxis
          tick={AXIS_TICK}
          axisLine={false}
          tickLine={false}
          width={78}
          domain={['auto', 'auto']}
          tickFormatter={(v: number) => formatBRL(v)}
        />
        <Tooltip
          content={({ active, payload, label }) => (
            <ChartTooltip
              active={active}
              label={label as string}
              rows={(payload ?? [])
                .filter((p) => p.value !== null && p.value !== undefined)
                .map((p) => ({
                  name: CHANNEL_LABEL[p.dataKey as Channel],
                  value: formatBRL(p.value as number),
                  color: CHANNEL_STYLE[p.dataKey as Channel].color,
                }))}
            />
          )}
        />
        <Legend
          content={() => (
            <ul className="flex flex-wrap justify-center gap-4 pt-1 text-xs text-ink">
              {channels.map((c) => (
                <li key={c} className="flex items-center gap-1.5">
                  <svg width="22" height="8" aria-hidden>
                    <line
                      x1="1"
                      y1="4"
                      x2="21"
                      y2="4"
                      stroke={CHANNEL_STYLE[c].color}
                      strokeWidth="2"
                      strokeDasharray={CHANNEL_STYLE[c].dash}
                    />
                  </svg>
                  {CHANNEL_LABEL[c]}
                </li>
              ))}
            </ul>
          )}
        />
        {channels.map((c) => (
          <Line
            key={c}
            type="stepAfter"
            dataKey={c}
            stroke={CHANNEL_STYLE[c].color}
            strokeWidth={2}
            strokeDasharray={CHANNEL_STYLE[c].dash}
            dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
            activeDot={{ r: 5 }}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
