import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import {
  useCreateUnitExceptions,
  useDeleteUnitException,
  useUnitExceptions,
  useUpdateUnitException,
} from '../../api/units.queries';
import {
  emptyExceptionForm,
  exceptionInput,
  exceptionToForm,
  exceptionUpdate,
  formatPeriod,
  validateException,
  type ExceptionErrors,
  type ExceptionForm,
} from '../../model/unit.rules';
import type { UnitException, UnitRecord } from '../../model/unit.types';
import HolidaysDialog from './HolidaysDialog';

interface UnitExceptionsSectionProps {
  unit: UnitRecord;
  /** Other units the user configures — offered in "Aplicar também em". */
  otherConfigurable: UnitRecord[];
  canEdit: boolean;
}

function localToday(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

/** "Feriados e datas especiais" of the open unit: list, form and suggested holidays. */
export default function UnitExceptionsSection({ unit, otherConfigurable, canEdit }: UnitExceptionsSectionProps) {
  const exceptions = useUnitExceptions(unit.id);
  const create = useCreateUnitExceptions();
  const update = useUpdateUnitException();
  const remove = useDeleteUnitException();
  const today = localToday();
  const year = Number(today.slice(0, 4));

  const [editing, setEditing] = useState<UnitException | 'new' | null>(null);
  const [form, setForm] = useState<ExceptionForm>(() => emptyExceptionForm(today));
  const [errors, setErrors] = useState<ExceptionErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<UnitException | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState<number | null>(null);

  function set<K extends keyof ExceptionForm>(key: K, value: ExceptionForm[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function open(target: UnitException | 'new') {
    setEditing(target);
    setErrors({});
    setSubmitError(null);
    setForm(
      target === 'new'
        ? emptyExceptionForm(today, otherConfigurable.length ? otherConfigurable.map((u) => u.id) : [])
        : exceptionToForm(target),
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateException(form, today);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      if (editing === 'new') await create.mutateAsync(exceptionInput(form, unit.id));
      else if (editing) await update.mutateAsync({ id: editing.id, input: exceptionUpdate(form) });
      setEditing(null);
    } catch (err) {
      if (statusOf(err) === 409) setErrors({ period: errorMessage(err) });
      else setSubmitError(errorMessage(err));
    }
  }

  async function confirmDelete() {
    if (!deleting) return;
    setDeleteError(null);
    try {
      await remove.mutateAsync(deleting.id);
      setDeleting(null);
    } catch (err) {
      setDeleteError(errorMessage(err));
    }
  }

  const busy = create.isPending || update.isPending;

  return (
    <section className="panel form-panel">
      <div className="panel-head">
        <div className="panel-title">Feriados e datas especiais</div>
        {canEdit ? (
          <span className="row-actions">
            <button type="button" className="btn btn-sm" onClick={() => setSuggesting(year)}>
              Sugerir feriados de {year}
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setSuggesting(year + 1)}>
              {year + 1}
            </button>
            <button type="button" className="btn-primary" onClick={() => open('new')}>
              Nova data
            </button>
          </span>
        ) : (
          <span className="cell-muted">Somente leitura</span>
        )}
      </div>

      {exceptions.isError ? (
        <div className="form-alert" role="alert">
          {errorMessage(exceptions.error)}{' '}
          <button type="button" className="btn btn-sm" onClick={() => void exceptions.refetch()}>
            Tentar de novo
          </button>
        </div>
      ) : null}

      <ul className="exception-list">
        {exceptions.isPending ? (
          <li>
            <span className="skeleton-bar" />
          </li>
        ) : null}
        {exceptions.isSuccess && exceptions.data.length === 0 ? (
          <li className="cell-muted">Nenhum feriado ou data especial cadastrada.</li>
        ) : null}
        {exceptions.data?.map((x) => (
          <li key={x.id} className="exception-item">
            <span className="exception-period tnum">{formatPeriod(x.starts_on, x.ends_on, year)}</span>
            <span className={x.kind === 'closed' ? 'badge badge-cancelado' : 'badge badge-pendente'}>
              {x.kind === 'closed' ? 'Fechado' : `Aberto ${x.opens_at}–${x.closes_at}`}
            </span>
            <span className="cell-muted exception-reason">{x.reason ?? ''}</span>
            {canEdit ? (
              <span className="row-actions">
                <button type="button" className="btn btn-sm" onClick={() => open(x)}>
                  Editar
                </button>
                <button type="button" className="btn btn-sm" onClick={() => setDeleting(x)}>
                  Apagar
                </button>
              </span>
            ) : null}
          </li>
        ))}
      </ul>

      {editing ? (
        <form className="exception-form" onSubmit={(e) => void submit(e)} noValidate>
          {submitError ? (
            <div className="form-alert" role="alert">
              {submitError}
            </div>
          ) : null}
          <div className="form-grid">
            <label className="field">
              <span className="field-label">De</span>
              <input
                type="date"
                className={`input${errors.period ? ' is-invalid' : ''}`}
                value={form.startsOn}
                min={today}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    startsOn: e.target.value,
                    endsOn: f.endsOn < e.target.value ? e.target.value : f.endsOn,
                  }))
                }
              />
            </label>
            <label className="field">
              <span className="field-label">Até</span>
              <input
                type="date"
                className={`input${errors.period ? ' is-invalid' : ''}`}
                value={form.endsOn}
                min={form.startsOn}
                onChange={(e) => set('endsOn', e.target.value)}
              />
              {errors.period ? <span className="field-error">{errors.period}</span> : null}
            </label>
            <label className="field">
              <span className="field-label">Tipo</span>
              <select
                className="select"
                value={form.kind}
                onChange={(e) => set('kind', e.target.value as ExceptionForm['kind'])}
              >
                <option value="closed">Fechado</option>
                <option value="special_hours">Horário especial</option>
              </select>
            </label>
            {form.kind === 'special_hours' ? (
              <label className="field">
                <span className="field-label">Horário</span>
                <span className="week-interval">
                  <input
                    type="time"
                    step={300}
                    className={`input input-time${errors.hours ? ' is-invalid' : ''}`}
                    aria-label="Abre às"
                    value={form.opensAt}
                    onChange={(e) => set('opensAt', e.target.value)}
                  />
                  <span aria-hidden="true">–</span>
                  <input
                    type="time"
                    step={300}
                    className={`input input-time${errors.hours ? ' is-invalid' : ''}`}
                    aria-label="Fecha às"
                    value={form.closesAt}
                    onChange={(e) => set('closesAt', e.target.value)}
                  />
                </span>
                {errors.hours ? <span className="field-error">{errors.hours}</span> : null}
              </label>
            ) : null}
            <label className="field field-full">
              <span className="field-label">Motivo (opcional)</span>
              <input
                className={`input${errors.reason ? ' is-invalid' : ''}`}
                value={form.reason}
                maxLength={120}
                placeholder="Ex.: feriado municipal, reforma"
                onChange={(e) => set('reason', e.target.value)}
              />
              <span className="field-hint">O atendimento automático usa este motivo para explicar ao cliente.</span>
              {errors.reason ? <span className="field-error">{errors.reason}</span> : null}
            </label>
            {editing === 'new' && otherConfigurable.length ? (
              <div className="field-full">
                <div className="field-label" style={{ marginBottom: 7 }}>
                  Aplicar também em
                </div>
                <div className="chip-row">
                  {otherConfigurable.map((u) => {
                    const on = form.alsoUnitIds.includes(u.id);
                    return (
                      <button
                        type="button"
                        key={u.id}
                        aria-pressed={on}
                        className={`chip${on ? ' is-on' : ''}`}
                        onClick={() =>
                          set('alsoUnitIds', on ? form.alsoUnitIds.filter((id) => id !== u.id) : [...form.alsoUnitIds, u.id])
                        }
                      >
                        {u.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </div>
          <div className="panel-foot">
            <button type="button" className="btn" onClick={() => setEditing(null)} disabled={busy}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={busy}>
              {busy ? 'Salvando…' : editing === 'new' ? 'Adicionar' : 'Salvar alterações'}
            </button>
          </div>
        </form>
      ) : null}

      {deleting ? (
        <ConfirmDialog
          title="Apagar esta data?"
          confirmLabel="Apagar"
          danger
          busy={remove.isPending}
          error={deleteError}
          onConfirm={() => void confirmDelete()}
          onCancel={() => {
            setDeleting(null);
            setDeleteError(null);
          }}
        >
          <p>
            {formatPeriod(deleting.starts_on, deleting.ends_on, year)} volta a seguir o horário de
            funcionamento normal.
          </p>
        </ConfirmDialog>
      ) : null}

      {suggesting !== null ? (
        <HolidaysDialog unitId={unit.id} year={suggesting} today={today} onClose={() => setSuggesting(null)} />
      ) : null}
    </section>
  );
}
