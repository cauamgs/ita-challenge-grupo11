import { useState } from 'react'
import { useImportRound } from '../../api/mutations'
import { useSession } from '../../app/session'
import { formatDate } from '../../lib/format'
import { Button } from '../Button'
import { FieldLabel } from '../Field'
import { Modal } from '../Modal'
import { useToast } from '../Toast'

interface RowError {
  linha: number | null
  campo: string | null
  erro: string
}

export function ImportRoundButton() {
  const { currentUser, setCurrentRoundId } = useSession()
  const toast = useToast()
  const mutation = useImportRound()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [replace, setReplace] = useState(false)

  const close = () => {
    setOpen(false)
    setFile(null)
    setReplace(false)
    mutation.reset()
  }

  const submit = () => {
    if (!file) return
    mutation.mutate(
      { file, replace, userId: currentUser?.id },
      {
        onSuccess: (result) => {
          setCurrentRoundId(result.round_id)
          toast({
            tone: 'success',
            title: `Rodada de ${formatDate(result.round_date)} importada`,
            lines: [`${result.imported} recomendações carregadas.`],
          })
          close()
        },
      },
    )
  }

  const errors = (mutation.error?.errors ?? []) as RowError[]
  const conflict = mutation.error?.status === 409

  return (
    <>
      <Button variant="ghost" onClick={() => setOpen(true)}>
        Importar rodada
      </Button>
      <Modal
        open={open}
        title="Importar rodada"
        onClose={close}
        footer={
          <>
            <Button variant="ghost" onClick={close}>
              Cancelar
            </Button>
            <Button disabled={!file || mutation.isPending} onClick={submit}>
              {mutation.isPending ? 'Importando…' : 'Importar'}
            </Button>
          </>
        }
      >
        <p className="text-xs text-ink-muted">
          Envie um CSV no formato de <code>recomendacoes_rodada_AAAA-MM-DD.csv</code>. A data da
          rodada vem da coluna <code>rodada_data</code>.
        </p>
        <label className="block">
          <FieldLabel>Arquivo CSV</FieldLabel>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null)
              mutation.reset()
            }}
            className="block w-full text-[13px] file:mr-3 file:h-8 file:rounded file:border-0 file:bg-brand-purpleLight file:px-3 file:font-semibold file:text-brand-purple"
          />
        </label>
        <label className="flex items-center gap-2 text-[13px]">
          <input
            type="checkbox"
            className="h-4 w-4 accent-brand-purple"
            checked={replace}
            onChange={(e) => setReplace(e.target.checked)}
          />
          Substituir a rodada se já existir nessa data (só se ainda não tiver decisões)
        </label>
        {mutation.error && (
          <div
            role="alert"
            className="rounded-card border-l-4 border-[#E07A74] bg-tag-baixar px-3 py-2 text-xs"
          >
            <p className="font-bold">{mutation.error.message}</p>
            {conflict && !replace && <p>Marque “Substituir” para importar novamente essa data.</p>}
            {errors.length > 0 && (
              <ul className="mt-1 max-h-40 list-disc overflow-y-auto pl-4">
                {errors.slice(0, 50).map((e, i) => (
                  <li key={i}>
                    {e.linha ? `Linha ${e.linha}` : 'Arquivo'}
                    {e.campo ? ` · ${e.campo}` : ''}: {e.erro}
                  </li>
                ))}
                {errors.length > 50 && <li>… e mais {errors.length - 50} erro(s).</li>}
              </ul>
            )}
          </div>
        )}
      </Modal>
    </>
  )
}
