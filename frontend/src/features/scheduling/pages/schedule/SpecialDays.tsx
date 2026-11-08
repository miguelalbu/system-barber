import { useState } from 'react';
import { errorMessage } from '@/shared/api/errorMessage';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useDeleteShiftOverride, useSaveShiftOverride, useShiftOverrides } from '../../api/schedule.queries';
import { daySummary, dayFormError, overrideIntervals, type Pause } from '../../model/schedule.rules';
import { localToday } from '../../model/today';

/** "Dias especiais": a different shift on one date, instead of the weekly schedule. */
export default function SpecialDays({ barberId, canEdit }: { barberId: string; canEdit: boolean }) {
  const today = localToday();
  const overrides = useShiftOverrides(barberId);
  const save = useSaveShiftOverride(barberId);
  const remove = useDeleteShiftOverride(barberId);
  const [adding, setAdding] = useState(false);
  const [date, setDate] = useState(today);
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('13:00');
  const [pause, setPause] = useState<Pause | null>(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [removing, setRemoving] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const problem =
      date < today
        ? 'Data no passado'
        : dayFormError({ weekday: 1, works: true, start, end, pauses: pause ? [pause] : [] });
    if (problem) {
      setError(problem);
      return;
    }
    try {
      const saved = await save.mutateAsync({ date, intervals: overrideIntervals(start, end, pause), reason: reason.trim() || null });
      setWarnings(saved.warnings);
      setAdding(false);
      setReason('');
      setPause(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section className="panel form-panel">
      <div className="panel-head">
        <div className="panel-title">Dias especiais</div>
        {canEdit && !adding ? (
          <button type="button" className="btn btn-sm" onClick={() => setAdding(true)}>
            Adicionar dia especial
          </button>
        ) : null}
      </div>
      {warnings.length ? (
        <div className="form-warning" role="status">
          {warnings.join(' · ')}
        </div>
      ) : null}
      <ul className="exception-list">
        {overrides.isPending ? (
          <li>
            <span className="skeleton-bar" />
          </li>
        ) : null}
        {overrides.isError ? <li className="field-error">{errorMessage(overrides.error)}</li> : null}
        {overrides.isSuccess && overrides.data.length === 0 ? (
          <li className="cell-muted">Nenhum dia especial nos próximos 90 dias.</li>
        ) : null}
        {overrides.data?.map((o) => (
          <li key={o.date} className="exception-item">
            <span className="exception-period tnum">
              {o.date.slice(8, 10)}/{o.date.slice(5, 7)}
            </span>
            <span className="badge badge-pendente">{daySummary(o.intervals)}</span>
            <span className="cell-muted exception-reason">{o.reason ?? ''}</span>
            {canEdit ? (
              <span className="row-actions">
                <button type="button" className="btn btn-sm" onClick={() => setRemoving(o.date)}>
                  Remover
                </button>
              </span>
            ) : null}
          </li>
        ))}
      </ul>

      {adding ? (
        <form className="exception-form" onSubmit={(e) => void submit(e)} noValidate>
          {error ? (
            <div className="form-alert" role="alert">
              {error}
            </div>
          ) : null}
          <div className="form-grid">
            <label className="field">
              <span className="field-label">Data</span>
              <input type="date" className="input" min={today} value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Horário</span>
              <span className="week-interval">
                <input type="time" step={300} className="input input-time" aria-label="Início" value={start} onChange={(e) => setStart(e.target.value)} />
                <span aria-hidden="true">–</span>
                <input type="time" step={300} className="input input-time" aria-label="Fim" value={end} onChange={(e) => setEnd(e.target.value)} />
              </span>
            </label>
            <label className="field">
              <span className="field-label">Pausa (opcional)</span>
              {pause ? (
                <span className="week-interval">
                  <input type="time" step={300} className="input input-time" aria-label="Pausa, início" value={pause.start} onChange={(e) => setPause({ ...pause, start: e.target.value })} />
                  <span aria-hidden="true">–</span>
                  <input type="time" step={300} className="input input-time" aria-label="Pausa, fim" value={pause.end} onChange={(e) => setPause({ ...pause, end: e.target.value })} />
                  <button type="button" className="btn-quiet" aria-label="Remover pausa" onClick={() => setPause(null)}>
                    ✕
                  </button>
                </span>
              ) : (
                <button type="button" className="btn-link" onClick={() => setPause({ start: '12:00', end: '13:00' })}>
                  + pausa
                </button>
              )}
            </label>
            <label className="field field-full">
              <span className="field-label">Motivo (opcional)</span>
              <input className="input" maxLength={120} value={reason} onChange={(e) => setReason(e.target.value)} />
              <span className="field-hint">Substitui a escala só nesse dia. Não abre a unidade se ela estiver fechada.</span>
            </label>
          </div>
          <div className="panel-foot">
            <button type="button" className="btn" onClick={() => setAdding(false)} disabled={save.isPending}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={save.isPending}>
              {save.isPending ? 'Salvando…' : 'Salvar dia especial'}
            </button>
          </div>
        </form>
      ) : null}

      {removing ? (
        <ConfirmDialog
          title="Remover este dia especial?"
          confirmLabel="Remover"
          busy={remove.isPending}
          error={remove.error ? errorMessage(remove.error) : null}
          onConfirm={() => void remove.mutateAsync(removing).then(() => setRemoving(null))}
          onCancel={() => setRemoving(null)}
        >
          <p>Nesse dia o barbeiro volta a seguir a escala semanal.</p>
        </ConfirmDialog>
      ) : null}
    </section>
  );
}
