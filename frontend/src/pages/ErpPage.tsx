import { useEffect, useState, type ReactNode } from 'react'
import {
  useErpStatus,
  useErpSyncs,
  useImportErpFile,
  useSaveSchedule,
  useSchedulePreview,
  useSyncNow,
} from '../api/platform'
import type { ScheduleInput, SyncFrequency, SyncRun } from '../api/types'
import { useSession } from '../app/session'
import { Button } from '../components/Button'
import { Card, PageHeader } from '../components/Card'
import { fieldClass, FieldLabel } from '../components/Field'
import { Modal } from '../components/Modal'
import { Pagination } from '../components/Pagination'
import { Callout, EmptyState, ErrorBox, Loading, SkeletonRows } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { SyncStatusTag, SyncTriggerTag } from '../components/Tag'
import { useToast } from '../components/Toast'
import { formatDate, formatDateTime, formatRelative, formatWeekdayDateTime } from '../lib/format'
import { FREQUENCY_LABEL, WEEKDAY_LABEL } from '../lib/labels'

function runToast(run: SyncRun) {
  return run.status === 'SUCESSO'
    ? {
        tone: 'success' as const,
        title: 'Sincronização concluída',
        lines: run.message ? [run.message] : [],
      }
    : {
        tone: 'error' as const,
        title: 'A sincronização falhou',
        lines: run.message ? [run.message] : [],
      }
}

function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-muted">{label}</dt>
      <dd className="tabular text-[15px] font-bold text-brand-purple">{value}</dd>
    </div>
  )
}

function ImportErpModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { currentUser } = useSession()
  const toast = useToast()
  const mutation = useImportErpFile()
  const [file, setFile] = useState<File | null>(null)
  const close = () => {
    setFile(null)
    mutation.reset()
    onClose()
  }
  const result = mutation.data
  return (
    <Modal
      open={open}
      title="Importar arquivo do ERP"
      onClose={close}
      footer={
        <>
          <Button variant="ghost" onClick={close}>
            {result?.status === 'SUCESSO' ? 'Fechar' : 'Cancelar'}
          </Button>
          <Button
            disabled={!file || mutation.isPending}
            onClick={() =>
              file &&
              mutation.mutate(
                { file, userId: currentUser?.id },
                {
                  onSuccess: (run) => {
                    if (run.status === 'SUCESSO') {
                      toast(runToast(run))
                      close()
                    }
                  },
                },
              )
            }
          >
            {mutation.isPending ? 'Importando…' : 'Importar'}
          </Button>
        </>
      }
    >
      <p className="text-xs text-ink-muted">
        Envie a planilha exportada do ERP (.xlsx) no mesmo layout da base: abas Produtos,
        Precos_Atuais, Custos_Margens, Estoque e, opcionalmente, Historico_Precos. O cadastro, os
        preços por canal e o estoque são atualizados, e toda mudança de preço entra no histórico do
        SKU.
      </p>
      <label className="block">
        <FieldLabel>Arquivo .xlsx</FieldLabel>
        <input
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null)
            mutation.reset()
          }}
          className="block w-full text-[13px] file:mr-3 file:h-8 file:rounded file:border-0 file:bg-brand-purpleLight file:px-3 file:font-semibold file:text-brand-purple"
        />
      </label>
      {mutation.error && <ErrorBox error={mutation.error} />}
      {result?.status === 'ERRO' && (
        <div
          role="alert"
          className="rounded-card border-l-4 border-[#E07A74] bg-tag-baixar px-3 py-2 text-xs"
        >
          <p className="font-bold">A importação falhou e nada foi alterado.</p>
          <p>{result.message}</p>
        </div>
      )}
    </Modal>
  )
}

const FREQUENCIES: SyncFrequency[] = ['DIARIA', 'SEMANAL', 'MENSAL']

function ScheduleCard() {
  const { currentUser } = useSession()
  const toast = useToast()
  const { data: status } = useErpStatus()
  const save = useSaveSchedule()
  const [form, setForm] = useState<ScheduleInput | null>(null)

  useEffect(() => {
    if (status && form === null) {
      const s = status.schedule
      setForm({
        enabled: s.enabled,
        frequency: s.frequency,
        weekday: s.weekday ?? 0,
        day_of_month: s.day_of_month ?? 10,
        time_of_day: s.time_of_day,
      })
    }
  }, [status, form])

  const payload: ScheduleInput | null = form && {
    ...form,
    weekday: form.frequency === 'SEMANAL' ? form.weekday : null,
    day_of_month: form.frequency === 'MENSAL' ? form.day_of_month : null,
  }
  const preview = useSchedulePreview(
    payload ?? ({} as ScheduleInput),
    !!payload && /^\d{2}:\d{2}$/.test(payload.time_of_day),
  )
  if (!status || !form || !payload)
    return (
      <Card title="Sincronização automática">
        <Loading />
      </Card>
    )

  const saved = status.schedule
  const dirty =
    saved.enabled !== payload.enabled ||
    saved.frequency !== payload.frequency ||
    saved.weekday !== payload.weekday ||
    saved.day_of_month !== payload.day_of_month ||
    saved.time_of_day !== payload.time_of_day
  const set = (patch: Partial<ScheduleInput>) => setForm({ ...form, ...patch })

  return (
    <Card
      title="Sincronização automática"
      subtitle="Puxa a base de produtos do ERP sem ninguém precisar clicar"
      action={
        <label className="flex cursor-pointer items-center gap-2 text-[13px] font-semibold">
          <span>{form.enabled ? 'Ativada' : 'Desativada'}</span>
          <button
            type="button"
            role="switch"
            aria-checked={form.enabled}
            aria-label="Ativar sincronização automática"
            onClick={() => set({ enabled: !form.enabled })}
            className={`relative h-6 w-11 rounded-full transition ${form.enabled ? 'bg-brand-purple' : 'bg-[#CFCFCF]'}`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${form.enabled ? 'left-[22px]' : 'left-0.5'}`}
            />
          </button>
        </label>
      }
    >
      <fieldset disabled={!form.enabled} className="space-y-3 disabled:opacity-50">
        <div>
          <FieldLabel>Frequência</FieldLabel>
          <div
            className="inline-flex rounded border border-brand-purpleLine p-0.5"
            role="radiogroup"
          >
            {FREQUENCIES.map((f) => (
              <button
                key={f}
                type="button"
                role="radio"
                aria-checked={form.frequency === f}
                onClick={() => set({ frequency: f })}
                className={`h-7 rounded px-4 text-[13px] font-semibold ${form.frequency === f ? 'bg-brand-purple text-white' : 'text-brand-purple hover:bg-brand-purpleLight'}`}
              >
                {FREQUENCY_LABEL[f]}
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          {form.frequency === 'SEMANAL' && (
            <label>
              <FieldLabel>Dia da semana</FieldLabel>
              <select
                className={fieldClass}
                value={form.weekday ?? 0}
                onChange={(e) => set({ weekday: Number(e.target.value) })}
              >
                {WEEKDAY_LABEL.map((label, i) => (
                  <option key={label} value={i}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {form.frequency === 'MENSAL' && (
            <label>
              <FieldLabel>Dia do mês</FieldLabel>
              <select
                className={fieldClass}
                value={form.day_of_month ?? 10}
                onChange={(e) => set({ day_of_month: Number(e.target.value) })}
              >
                {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                  <option key={day} value={day}>
                    Todo dia {day}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            <FieldLabel>Horário</FieldLabel>
            <input
              type="time"
              className={`${fieldClass} tabular`}
              value={form.time_of_day}
              onChange={(e) => set({ time_of_day: e.target.value })}
            />
          </label>
          {form.frequency === 'MENSAL' && (
            <div className="flex gap-1 pb-1 text-xs">
              {[1, 10, 15, 20].map((day) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => set({ day_of_month: day })}
                  className={`rounded-full border px-2 py-0.5 ${form.day_of_month === day ? 'border-brand-purple bg-brand-purpleLight font-bold text-brand-purple' : 'border-line text-ink-muted hover:border-brand-purpleLine'}`}
                >
                  dia {day}
                </button>
              ))}
            </div>
          )}
        </div>
      </fieldset>

      <div className="mt-3 rounded-card bg-brand-purpleLight px-3 py-2 text-[13px]">
        {form.enabled ? (
          preview.data ? (
            <>
              <strong>{preview.data.description}.</strong> Próxima execução:{' '}
              <strong>{formatWeekdayDateTime(preview.data.next_run_at)}</strong>{' '}
              <span className="text-ink-muted">({formatRelative(preview.data.next_run_at)})</span>
            </>
          ) : preview.error ? (
            <span className="text-[#B3261E]">{(preview.error as Error).message}</span>
          ) : (
            'Calculando a próxima execução…'
          )
        ) : (
          'A sincronização automática está desligada. A base só é atualizada por “Sincronizar agora” ou por importação de arquivo.'
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-ink-muted">
          {saved.updated_at
            ? `Última alteração por ${saved.updated_by_name ?? '—'} em ${formatDateTime(saved.updated_at)}`
            : 'Configuração padrão (nunca alterada)'}
          {saved.last_run_at &&
            ` · última execução automática ${formatRelative(saved.last_run_at)}`}
        </p>
        <div className="flex gap-2">
          {dirty && (
            <Button variant="ghost" onClick={() => setForm(null)}>
              Descartar
            </Button>
          )}
          <Button
            disabled={!dirty || save.isPending}
            onClick={() =>
              save.mutate(
                { ...payload, user_id: currentUser?.id ?? null },
                {
                  onSuccess: (s) => {
                    toast({
                      tone: 'success',
                      title: s.enabled
                        ? 'Sincronização automática salva'
                        : 'Sincronização automática desligada',
                      lines: s.enabled
                        ? [`${s.description} · próxima: ${formatWeekdayDateTime(s.next_run_at)}`]
                        : [],
                    })
                    setForm(null)
                  },
                  onError: (e) => toast({ tone: 'error', title: e.message }),
                },
              )
            }
          >
            Salvar configuração
          </Button>
        </div>
      </div>
    </Card>
  )
}

function SyncHistory() {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useErpSyncs(page)
  if (error) return <ErrorBox error={error} />
  return (
    <Card
      title="Histórico de sincronizações"
      subtitle="Toda execução fica registrada, com sucesso ou erro"
    >
      <TableContainer>
        <thead>
          <tr>
            <Th>Data/hora</Th>
            <Th>Origem</Th>
            <Th>Usuário</Th>
            <Th>Status</Th>
            <Th>Fonte</Th>
            <Th numeric>Produtos</Th>
            <Th numeric>Novos</Th>
            <Th numeric>Atualizados</Th>
            <Th numeric>Preços alterados</Th>
            <Th numeric>Duração</Th>
            <Th>Resultado</Th>
          </tr>
        </thead>
        <tbody>
          {isLoading && <SkeletonRows cols={11} rows={4} />}
          {!isLoading && data?.items.length === 0 && (
            <tr>
              <td colSpan={11}>
                <EmptyState title="Nenhuma sincronização ainda" />
              </td>
            </tr>
          )}
          {data?.items.map((run, i) => (
            <tr key={run.id} className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}>
              <Td className="tabular whitespace-nowrap">{formatDateTime(run.started_at)}</Td>
              <Td>
                <SyncTriggerTag value={run.trigger} />
              </Td>
              <Td className="whitespace-nowrap">
                {run.user_name ?? (run.trigger === 'AGENDADO' ? 'Agendador' : 'Sistema')}
              </Td>
              <Td>
                <SyncStatusTag value={run.status} />
              </Td>
              <Td className="max-w-[220px] truncate">
                <span title={run.source}>{run.source}</span>
              </Td>
              <Td numeric>{run.products_total}</Td>
              <Td numeric>{run.products_new}</Td>
              <Td numeric>{run.products_updated}</Td>
              <Td numeric className={run.prices_changed ? 'font-bold text-brand-purple' : ''}>
                {run.prices_changed}
              </Td>
              <Td numeric>
                {run.duration_seconds !== null ? `${run.duration_seconds.toFixed(1)} s` : '—'}
              </Td>
              <Td className="min-w-[260px] text-xs">{run.message ?? '—'}</Td>
            </tr>
          ))}
        </tbody>
      </TableContainer>
      <Pagination page={page} pageSize={10} total={data?.total ?? 0} onChange={setPage} />
    </Card>
  )
}

export function ErpPage() {
  const { currentUser } = useSession()
  const toast = useToast()
  const { data: status, isLoading, error } = useErpStatus()
  const sync = useSyncNow()
  const [importOpen, setImportOpen] = useState(false)

  if (isLoading) return <Loading />
  if (error || !status) return <ErrorBox error={error} />
  const last = status.last_sync

  return (
    <div className="space-y-4">
      <PageHeader
        kicker="Integração"
        title="Base de produtos do ERP"
        description="Produtos, preços por canal, custos, estoque e histórico de preços vêm do ERP da Popular Pet."
        actions={
          <>
            <Button variant="ghost" onClick={() => setImportOpen(true)}>
              Importar arquivo do ERP
            </Button>
            <Button
              disabled={sync.isPending}
              onClick={() =>
                sync.mutate(
                  { userId: currentUser?.id },
                  {
                    onSuccess: (run) => toast(runToast(run)),
                    onError: (e) => toast({ tone: 'error', title: e.message }),
                  },
                )
              }
            >
              {sync.isPending ? 'Sincronizando…' : 'Sincronizar agora'}
            </Button>
          </>
        }
      />

      <div className="grid gap-3 lg:grid-cols-[2fr_3fr]">
        <Card title="Situação da integração">
          <div className="flex items-center gap-2 text-[13px]">
            <span className="inline-flex h-2.5 w-2.5 rounded-full bg-brand-lime" aria-hidden />
            <strong>{status.source}</strong>
            <span className="text-ink-muted">· {status.source_file}</span>
          </div>
          {last ? (
            <div className="mt-3 rounded-card border border-line p-3 text-[13px]">
              <div className="flex flex-wrap items-center gap-2">
                <SyncStatusTag value={last.status} />
                <SyncTriggerTag value={last.trigger} />
                <span className="text-ink-muted">
                  {formatDateTime(last.started_at)} ({formatRelative(last.started_at)})
                </span>
              </div>
              <p className="mt-1">{last.message}</p>
            </div>
          ) : (
            <p className="mt-3 text-ink-muted">A base ainda não foi sincronizada.</p>
          )}
          <dl className="mt-3 grid grid-cols-2 gap-3">
            <Stat label="Produtos no cadastro" value={status.products} />
            <Stat label="Preços por canal" value={status.channel_prices} />
            <Stat label="Alterações de preço registradas" value={status.price_changes} />
            <Stat label="Data de referência" value={formatDate(status.last_reference_date)} />
          </dl>
          {status.last_success && last?.status === 'ERRO' && (
            <p className="mt-2 text-xs text-ink-muted">
              Último sucesso: {formatDateTime(status.last_success.started_at)}. Os dados em uso são
              dessa sincronização.
            </p>
          )}
        </Card>
        <ScheduleCard />
      </div>

      <Callout tone="purple">
        <p className="text-xs">
          <strong>ERP simulado.</strong> Neste protótipo o “ERP” é a planilha{' '}
          <code>{status.source_file}</code> com os dados fictícios do desafio: “Sincronizar agora” e
          a sincronização automática leem esse arquivo. Para simular mudanças vindas do ERP (preço,
          cadastro, estoque), use “Importar arquivo do ERP” com uma versão alterada da planilha.
        </p>
      </Callout>

      <SyncHistory />
      <ImportErpModal open={importOpen} onClose={() => setImportOpen(false)} />
    </div>
  )
}
