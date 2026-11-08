import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import { useSaveTimeOff } from '../../api/schedule.queries';
import { TIME_OFF_LABELS, validateTimeOff, type TimeOffForm as Form } from '../../model/schedule.rules';
import type { AffectedAppointment, BarberRef, TimeOff } from '../../model/schedule.types';
import { localToday } from '../../model/today';

interface TimeOffFormProps {
  timeOff: TimeOff | null;
  barbers: BarberRef[];
  onClose: () => void;
  onSaved: (affected: AffectedAppointment[], barberName: string) => void;
}

const KINDS = ['day_off', 'vacation', 'sick_leave'] as const;

/** Create or edit a whole-day absence (folga, férias, atestado). */
export default function TimeOffForm({ timeOff, barbers, onClose, onSaved }: TimeOffFormProps) {
  const today = localToday();
  const [form, setForm] = useState<Form>(() =>
    timeOff
      ? {
          barberId: timeOff.barber_id,
          kind: timeOff.kind === 'block' ? 'day_off' : timeOff.kind,
          startsOn: timeOff.starts_on,
          endsOn: timeOff.ends_on,
          reason: timeOff.reason ?? '',
        }
      : { barberId: barbers[0]?.id ?? '', kind: 'day_off', startsOn: today, endsOn: today, reason: '' },
  );
  const [errors, setErrors] = useState<ReturnType<typeof validateTimeOff>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const save = useSaveTimeOff();

  function set<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateTimeOff(form, today);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      const result = await save.mutateAsync({
        id: timeOff?.id ?? null,
        input: {
          barber_id: form.barberId,
          kind: form.kind,
          starts_on: form.startsOn,
          ends_on: form.endsOn,
          reason: form.reason.trim() || null,
        },
      });
      onSaved(result.affected_appointments, barbers.find((b) => b.id === form.barberId)?.name ?? 'o barbeiro');
    } catch (err) {
      if (statusOf(err) === 409) setErrors({ period: errorMessage(err) });
      else setSubmitError(errorMessage(err));
    }
  }

  return (
    <form className="panel form-panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">{timeOff ? 'Editar ausência' : 'Nova ausência'}</div>
        <button type="button" className="btn-quiet" onClick={onClose}>
          Fechar
        </button>
      </div>
      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
        </div>
      ) : null}
      <div className="form-grid">
        <label className="field">
          <span className="field-label">Barbeiro</span>
          <select
            className={`select${errors.barberId ? ' is-invalid' : ''}`}
            value={form.barberId}
            disabled={timeOff !== null}
            onChange={(e) => set('barberId', e.target.value)}
          >
            {barbers.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
          {errors.barberId ? <span className="field-error">{errors.barberId}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Tipo</span>
          <select
            className="select"
            value={form.kind}
            disabled={timeOff !== null}
            onChange={(e) => set('kind', e.target.value as Form['kind'])}
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {TIME_OFF_LABELS[k]}
              </option>
            ))}
          </select>
        </label>
        <span />
        <label className="field">
          <span className="field-label">De</span>
          <input
            type="date"
            className={`input${errors.period ? ' is-invalid' : ''}`}
            min={today}
            value={form.startsOn}
            onChange={(e) =>
              setForm((f) => ({ ...f, startsOn: e.target.value, endsOn: f.endsOn < e.target.value ? e.target.value : f.endsOn }))
            }
          />
        </label>
        <label className="field">
          <span className="field-label">Até</span>
          <input
            type="date"
            className={`input${errors.period ? ' is-invalid' : ''}`}
            min={form.startsOn}
            value={form.endsOn}
            onChange={(e) => set('endsOn', e.target.value)}
          />
          {errors.period ? <span className="field-error">{errors.period}</span> : null}
        </label>
        <label className="field field-full">
          <span className="field-label">Motivo (opcional)</span>
          <input
            className={`input${errors.reason ? ' is-invalid' : ''}`}
            maxLength={200}
            value={form.reason}
            onChange={(e) => set('reason', e.target.value)}
          />
          <span className="field-hint">Só a equipe vê. Ao cliente, o atendimento diz apenas que o barbeiro não atende nesse dia.</span>
          {errors.reason ? <span className="field-error">{errors.reason}</span> : null}
        </label>
      </div>
      <div className="panel-foot">
        <button type="button" className="btn" onClick={onClose} disabled={save.isPending}>
          Cancelar
        </button>
        <button type="submit" className="btn-primary" disabled={save.isPending}>
          {save.isPending ? 'Salvando…' : timeOff ? 'Salvar alterações' : 'Registrar ausência'}
        </button>
      </div>
    </form>
  );
}
