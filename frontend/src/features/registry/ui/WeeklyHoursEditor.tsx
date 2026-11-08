import { MAX_INTERVALS, WEEKDAY_LABELS, copyToAllDays, nextInterval } from '../model/unit.rules';
import type { DayHours, Interval } from '../model/unit.types';

interface WeeklyHoursEditorProps {
  days: DayHours[];
  onChange: (days: DayHours[]) => void;
  /** Errors by weekday (from `weekErrors`). */
  errors?: Record<number, string>;
  readOnly?: boolean;
}

/**
 * One row per weekday: open or closed, up to three intervals. Controlled — the
 * parent keeps the week and decides when to save. Reused by the onboarding
 * wizard (S16), hence `ui/` and the export in `index.ts`.
 */
export default function WeeklyHoursEditor({
  days,
  onChange,
  errors = {},
  readOnly = false,
}: WeeklyHoursEditorProps) {
  function setDay(weekday: number, intervals: Interval[]) {
    onChange(days.map((d) => (d.weekday === weekday ? { weekday, intervals } : d)));
  }

  function setTime(day: DayHours, index: number, key: keyof Interval, value: string) {
    setDay(
      day.weekday,
      day.intervals.map((i, n) => (n === index ? { ...i, [key]: value } : i)),
    );
  }

  return (
    <div className="week-editor">
      {days.map((day) => {
        const open = day.intervals.length > 0;
        const label = WEEKDAY_LABELS[day.weekday];
        return (
          <div className={`week-row${errors[day.weekday] ? ' has-error' : ''}`} key={day.weekday}>
            <label className="week-day">
              <input
                type="checkbox"
                checked={open}
                disabled={readOnly}
                aria-label={`${label} aberto`}
                onChange={(e) => setDay(day.weekday, e.target.checked ? [nextInterval([])] : [])}
              />
              <span>{label}</span>
            </label>

            <div className="week-intervals">
              {open ? null : <span className="cell-muted">Fechado</span>}
              {day.intervals.map((interval, index) => (
                <span className="week-interval" key={index}>
                  <input
                    type="time"
                    step={300}
                    className="input input-time"
                    aria-label={`${label}, intervalo ${index + 1}, abre`}
                    value={interval.opens_at}
                    disabled={readOnly}
                    onChange={(e) => setTime(day, index, 'opens_at', e.target.value)}
                  />
                  <span aria-hidden="true">–</span>
                  <input
                    type="time"
                    step={300}
                    className="input input-time"
                    aria-label={`${label}, intervalo ${index + 1}, fecha`}
                    value={interval.closes_at}
                    disabled={readOnly}
                    onChange={(e) => setTime(day, index, 'closes_at', e.target.value)}
                  />
                  {readOnly ? null : (
                    <button
                      type="button"
                      className="btn-quiet"
                      aria-label={`Remover intervalo ${index + 1} de ${label}`}
                      onClick={() => setDay(day.weekday, day.intervals.filter((_, n) => n !== index))}
                    >
                      ✕
                    </button>
                  )}
                </span>
              ))}
              {errors[day.weekday] ? (
                <span className="field-error week-error">{errors[day.weekday]}</span>
              ) : null}
            </div>

            {readOnly ? null : (
              <div className="week-actions">
                {open && day.intervals.length < MAX_INTERVALS ? (
                  <button
                    type="button"
                    className="btn-link"
                    onClick={() => setDay(day.weekday, [...day.intervals, nextInterval(day.intervals)])}
                  >
                    + intervalo
                  </button>
                ) : null}
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => onChange(copyToAllDays(days, day.weekday))}
                >
                  Copiar para todos
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
