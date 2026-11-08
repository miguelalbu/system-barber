import { useState } from 'react';
import { errorMessage } from '@/shared/api/errorMessage';
import { useSaveSchedule } from '../../api/schedule.queries';
import {
  MAX_PAUSES,
  WEEKDAYS,
  copyMondayToWeekdays,
  formsToWeek,
  weekFormErrors,
  weekToForms,
  type DayForm,
} from '../../model/schedule.rules';
import type { BarberSchedule } from '../../model/schedule.types';
import SpecialDays from './SpecialDays';

interface WeekEditorProps {
  schedule: BarberSchedule;
  barberName: string;
  canEdit: boolean;
  onClose: () => void;
}

/** One barber's week as "works · start · end · pauses", saved whole. */
export default function WeekEditor({ schedule, barberName, canEdit, onClose }: WeekEditorProps) {
  const [forms, setForms] = useState<DayForm[]>(() => weekToForms(schedule.days));
  const [showErrors, setShowErrors] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const save = useSaveSchedule();
  const errors = weekFormErrors(forms);

  function setDay(weekday: number, patch: Partial<DayForm>) {
    setForms((all) => all.map((f) => (f.weekday === weekday ? { ...f, ...patch } : f)));
  }

  async function submit() {
    setShowErrors(true);
    setSubmitError(null);
    if (Object.keys(errors).length) return;
    try {
      const saved = await save.mutateAsync({ barberId: schedule.barber_id, week: formsToWeek(forms) });
      setWarnings(saved.warnings);
      setShowErrors(false);
    } catch (err) {
      setSubmitError(errorMessage(err));
    }
  }

  return (
    <>
      <section className="panel form-panel">
        <div className="panel-head">
          <div className="panel-title">Escala · {barberName}</div>
          <button type="button" className="btn-quiet" onClick={onClose}>
            Fechar
          </button>
        </div>
        {schedule.configured ? null : (
          <div className="form-warning" role="status">
            Sem escala salva: segue o horário da unidade. Ajuste e salve para definir a escala dele.
          </div>
        )}
        {submitError ? (
          <div className="form-alert" role="alert">
            {submitError}
          </div>
        ) : null}
        {showErrors && errors[0] ? (
          <div className="form-alert" role="alert">
            {errors[0]}
          </div>
        ) : null}
        {warnings.length ? (
          <div className="form-warning" role="status">
            {warnings.join(' · ')}
          </div>
        ) : null}

        <div className="panel-body week-editor">
          {forms.map((day) => {
            const label = WEEKDAYS[day.weekday - 1].label;
            const error = showErrors ? errors[day.weekday] : undefined;
            return (
              <div className={`week-row${error ? ' has-error' : ''}`} key={day.weekday}>
                <label className="week-day">
                  <input
                    type="checkbox"
                    checked={day.works}
                    disabled={!canEdit}
                    aria-label={`${label}: trabalha`}
                    onChange={(e) => setDay(day.weekday, { works: e.target.checked })}
                  />
                  <span>{label}</span>
                </label>
                <div className="week-intervals">
                  {day.works ? (
                    <>
                      <span className="week-interval">
                        <input
                          type="time"
                          step={300}
                          className="input input-time"
                          aria-label={`${label}: início`}
                          value={day.start}
                          disabled={!canEdit}
                          onChange={(e) => setDay(day.weekday, { start: e.target.value })}
                        />
                        <span aria-hidden="true">–</span>
                        <input
                          type="time"
                          step={300}
                          className="input input-time"
                          aria-label={`${label}: fim`}
                          value={day.end}
                          disabled={!canEdit}
                          onChange={(e) => setDay(day.weekday, { end: e.target.value })}
                        />
                      </span>
                      {day.pauses.map((p, i) => (
                        <span className="week-interval" key={i}>
                          <span className="cell-muted">pausa</span>
                          <input
                            type="time"
                            step={300}
                            className="input input-time"
                            aria-label={`${label}: pausa ${i + 1}, início`}
                            value={p.start}
                            disabled={!canEdit}
                            onChange={(e) =>
                              setDay(day.weekday, {
                                pauses: day.pauses.map((x, n) => (n === i ? { ...x, start: e.target.value } : x)),
                              })
                            }
                          />
                          <span aria-hidden="true">–</span>
                          <input
                            type="time"
                            step={300}
                            className="input input-time"
                            aria-label={`${label}: pausa ${i + 1}, fim`}
                            value={p.end}
                            disabled={!canEdit}
                            onChange={(e) =>
                              setDay(day.weekday, {
                                pauses: day.pauses.map((x, n) => (n === i ? { ...x, end: e.target.value } : x)),
                              })
                            }
                          />
                          {canEdit ? (
                            <button
                              type="button"
                              className="btn-quiet"
                              aria-label={`Remover pausa ${i + 1} de ${label}`}
                              onClick={() => setDay(day.weekday, { pauses: day.pauses.filter((_, n) => n !== i) })}
                            >
                              ✕
                            </button>
                          ) : null}
                        </span>
                      ))}
                    </>
                  ) : (
                    <span className="cell-muted">Folga</span>
                  )}
                  {error ? <span className="field-error week-error">{error}</span> : null}
                </div>
                {canEdit ? (
                  <div className="week-actions">
                    {day.works && day.pauses.length < MAX_PAUSES ? (
                      <button
                        type="button"
                        className="btn-link"
                        onClick={() => setDay(day.weekday, { pauses: [...day.pauses, { start: '12:00', end: '13:00' }] })}
                      >
                        + pausa
                      </button>
                    ) : null}
                    {day.weekday === 1 ? (
                      <button type="button" className="btn-link" onClick={() => setForms(copyMondayToWeekdays(forms))}>
                        Copiar para dias úteis
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
          <p className="field-hint section-note">
            Mudar a escala vale para todos os próximos dias. Agendamentos que ficarem fora aparecem destacados na
            agenda. Horários fora do funcionamento da unidade não são oferecidos aos clientes.
          </p>
        </div>

        {canEdit ? (
          <div className="panel-foot">
            <button type="button" className="btn" onClick={() => setForms(weekToForms(schedule.days))} disabled={save.isPending}>
              Desfazer
            </button>
            <button type="button" className="btn-primary" onClick={() => void submit()} disabled={save.isPending}>
              {save.isPending ? 'Salvando…' : 'Salvar escala'}
            </button>
          </div>
        ) : null}
      </section>

      <SpecialDays barberId={schedule.barber_id} canEdit={canEdit} />
    </>
  );
}
