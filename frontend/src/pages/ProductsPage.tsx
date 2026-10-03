import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCategories, useProducts } from '../api/platform'
import type { Channel, ProductFilters } from '../api/types'
import { PageHeader } from '../components/Card'
import { Select, TextInput } from '../components/Field'
import { Pagination } from '../components/Pagination'
import { EmptyState, ErrorBox, SkeletonRows } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { PriceChangeTag } from '../components/Tag'
import { formatBRL, formatDate, formatNumber } from '../lib/format'
import { CHANNEL_LABEL } from '../lib/labels'
import { useUrlState } from '../lib/useUrlState'

const PAGE_SIZE = 20
const CHANNELS: Channel[] = ['LOJA_FISICA', 'ECOMMERCE', 'MARKETPLACE']
const COLUMNS = 10

export function ProductsPage() {
  const url = useUrlState()
  const navigate = useNavigate()
  const { data: categories } = useCategories()
  const page = Math.max(1, Number(url.get('pagina')) || 1)
  const filters: ProductFilters = {
    q: url.get('q') || undefined,
    category: url.get('categoria') || undefined,
    abc_curve: (url.get('curva') || undefined) as ProductFilters['abc_curve'],
    status: url.get('status') || undefined,
    sort: url.get('ordem') === 'recentes' ? 'recentes' : 'sku',
    page,
    page_size: PAGE_SIZE,
  }
  const { data, isLoading, error } = useProducts(filters)
  const { set } = url
  const change = useCallback(
    (updates: Record<string, string>) => set(updates, { resetPage: true }),
    [set],
  )

  const [search, setSearch] = useState(url.get('q'))
  const q = url.get('q')
  useEffect(() => setSearch(q), [q])
  useEffect(() => {
    if (search === q) return
    const t = setTimeout(() => change({ q: search }), 300)
    return () => clearTimeout(t)
  }, [search, q, change])

  return (
    <div className="space-y-3">
      <PageHeader
        kicker="Catálogo"
        title="Produtos"
        description="Cadastro e preços por canal sincronizados do ERP. Clique em um produto para ver o histórico de preço."
      />
      <div className="flex flex-wrap items-center gap-2">
        <TextInput
          label="Buscar por SKU ou produto"
          type="search"
          placeholder="Buscar SKU ou produto"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-56"
        />
        <Select
          label="Categoria"
          value={url.get('categoria')}
          onChange={(e) => change({ categoria: e.target.value })}
        >
          <option value="">Categoria: todas</option>
          {categories?.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
        <Select
          label="Curva ABC"
          value={url.get('curva')}
          onChange={(e) => change({ curva: e.target.value })}
        >
          <option value="">Curva: todas</option>
          <option value="A">Curva A</option>
          <option value="B">Curva B</option>
          <option value="C">Curva C</option>
        </Select>
        <Select
          label="Status"
          value={url.get('status')}
          onChange={(e) => change({ status: e.target.value })}
        >
          <option value="">Status: todos</option>
          <option value="Ativo">Ativo</option>
          <option value="Descontinuando">Descontinuando</option>
        </Select>
        <Select
          label="Ordenar"
          value={url.get('ordem')}
          onChange={(e) => change({ ordem: e.target.value })}
        >
          <option value="">Ordenar por SKU</option>
          <option value="recentes">Alteração de preço mais recente</option>
        </Select>
      </div>

      {error ? (
        <ErrorBox error={error} />
      ) : (
        <TableContainer maxHeight="calc(100vh - 290px)">
          <thead>
            <tr>
              <Th>SKU · Produto</Th>
              <Th>Categoria</Th>
              <Th>Curva</Th>
              {CHANNELS.map((c) => (
                <Th key={c} numeric>
                  {CHANNEL_LABEL[c]}
                </Th>
              ))}
              <Th>Última alteração de preço</Th>
              <Th numeric>Alterações</Th>
              <Th numeric>Estoque</Th>
              <Th numeric>Pendências</Th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <SkeletonRows cols={COLUMNS} />}
            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={COLUMNS}>
                  <EmptyState title="Nenhum produto encontrado">
                    Ajuste os filtros ou sincronize a base com o ERP.
                  </EmptyState>
                </td>
              </tr>
            )}
            {!isLoading &&
              data?.items.map((p, i) => (
                <tr
                  key={p.sku}
                  tabIndex={0}
                  onClick={() => navigate(`/produtos/${p.sku}`)}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/produtos/${p.sku}`)}
                  className={`cursor-pointer border-b border-line ${i % 2 ? 'bg-zebra' : ''} hover:bg-brand-purpleLight`}
                >
                  <Td>
                    <span className="font-semibold">{p.sku}</span>
                    <span className="text-ink-muted"> · </span>
                    {p.name}
                    {p.status !== 'Ativo' && (
                      <span className="ml-2 rounded bg-tag-manter px-1.5 text-[11px] font-bold">
                        {p.status}
                      </span>
                    )}
                  </Td>
                  <Td>{p.category}</Td>
                  <Td className="text-center font-bold">{p.abc_curve}</Td>
                  {CHANNELS.map((c) => (
                    <Td key={c} numeric>
                      {formatBRL(p.prices.find((x) => x.channel === c)?.current_price)}
                    </Td>
                  ))}
                  <Td className="whitespace-nowrap">
                    {p.last_change ? (
                      <span className="flex items-center gap-2">
                        <PriceChangeTag
                          value={p.last_change.change_type}
                          variation={p.last_change.variation}
                        />
                        <span className="text-xs text-ink-muted">
                          {formatDate(p.last_change.effective_date)} ·{' '}
                          {CHANNEL_LABEL[p.last_change.channel]}
                        </span>
                      </span>
                    ) : (
                      <span className="text-xs text-ink-muted">sem alterações</span>
                    )}
                  </Td>
                  <Td numeric>{p.price_changes}</Td>
                  <Td numeric>
                    {p.stock_qty ?? '—'}
                    {p.coverage_days !== null && (
                      <span className="block text-[11px] text-ink-muted">
                        {formatNumber(p.coverage_days)} dias
                      </span>
                    )}
                  </Td>
                  <Td numeric>
                    {p.pending_recommendations > 0 ? (
                      <Link
                        to={`/recomendacoes?q=${p.sku}&status=PENDENTE`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-purple px-1.5 text-[11px] font-bold text-white"
                        title="Recomendações pendentes na rodada atual"
                      >
                        {p.pending_recommendations}
                      </Link>
                    ) : (
                      <span className="text-ink-faint">—</span>
                    )}
                  </Td>
                </tr>
              ))}
          </tbody>
        </TableContainer>
      )}
      <Pagination
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.total ?? 0}
        onChange={(p) => url.set({ pagina: p === 1 ? null : String(p) })}
      />
    </div>
  )
}
