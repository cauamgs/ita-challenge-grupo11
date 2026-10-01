import { useEffect, useState, type ReactNode } from 'react'
import { Select, TextInput } from '../Field'

export interface FilterValues {
  canal: string
  curva: string
  recomendacao: string
  risco: string
  status: string
  aprovacao: string
  q: string
}

export function RecommendationFiltersBar({
  values,
  onChange,
  actions,
}: {
  values: FilterValues
  onChange: (updates: Partial<FilterValues>) => void
  actions?: ReactNode
}) {
  const [search, setSearch] = useState(values.q)

  useEffect(() => setSearch(values.q), [values.q])
  useEffect(() => {
    if (search === values.q) return
    const timer = setTimeout(() => onChange({ q: search }), 300)
    return () => clearTimeout(timer)
  }, [search, values.q, onChange])

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Select
        label="Canal"
        value={values.canal}
        onChange={(e) => onChange({ canal: e.target.value })}
      >
        <option value="">Canal: todos</option>
        <option value="LOJA_FISICA">Loja física</option>
        <option value="ECOMMERCE">E-commerce</option>
        <option value="MARKETPLACE">Marketplace</option>
      </Select>
      <Select
        label="Curva ABC"
        value={values.curva}
        onChange={(e) => onChange({ curva: e.target.value })}
      >
        <option value="">Curva: todas</option>
        <option value="A">Curva A</option>
        <option value="B">Curva B</option>
        <option value="C">Curva C</option>
      </Select>
      <Select
        label="Recomendação"
        value={values.recomendacao}
        onChange={(e) => onChange({ recomendacao: e.target.value })}
      >
        <option value="">Recomendação: todas</option>
        <option value="SUBIR">SUBIR</option>
        <option value="BAIXAR">BAIXAR</option>
        <option value="MANTER">MANTER</option>
        <option value="REVISAR">REVISAR</option>
      </Select>
      <Select
        label="Risco"
        value={values.risco}
        onChange={(e) => onChange({ risco: e.target.value })}
      >
        <option value="">Risco: todos</option>
        <option value="BAIXO">Baixo</option>
        <option value="MEDIO">Médio</option>
        <option value="ALTO">Alto</option>
      </Select>
      <Select
        label="Status da decisão"
        value={values.status}
        onChange={(e) => onChange({ status: e.target.value })}
      >
        <option value="">Status: todos</option>
        <option value="PENDENTE">Pendente</option>
        <option value="DECIDIDO">Decidido</option>
      </Select>
      <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 px-1 text-[13px]">
        <input
          type="checkbox"
          className="h-4 w-4 accent-brand-purple"
          checked={values.aprovacao === '1'}
          onChange={(e) => onChange({ aprovacao: e.target.checked ? '1' : '' })}
        />
        Só exige aprovação
      </label>
      <TextInput
        label="Buscar por SKU ou produto"
        type="search"
        placeholder="Buscar SKU ou produto"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-52"
      />
      {actions && <div className="ml-auto flex items-center gap-2">{actions}</div>}
    </div>
  )
}
