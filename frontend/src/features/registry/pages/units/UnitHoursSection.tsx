import { useEffect, useReducer, useState } from 'react';
import { errorMessage } from '@/shared/api/errorMessage';
import { useSaveUnitHours, useUnitHours } from '../../api/units.queries';
import { fullWeek, weekErrors, weekInput } from '../../model/unit.rules';
import type { DayHours } from '../../model/unit.types';
import WeeklyHoursEditor from '../../ui/WeeklyHoursEditor';

type Action = { type: 'load'; days: DayHours[] } | { type: 'edit'; days: DayHours[] };

function reducer(_: DayHours[], action: Action): DayHours[] {
  return fullWeek(action.days);
}

/** "Horário de funcionamento" of the open unit: edit the week, save it whole. */
export default function UnitHoursSection({ unitId, canEdit }: { unitId: string; canEdit: boolean }) {
  const hours = useUnitHours(unitId);
  const save = useSaveUnitHours(unitId);
  const [days, dispatch] = useReducer(reducer, fullWeek([]));
  const [saved, setSaved] = useState<DayHours[]>(fullWeek([]));
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showErrors, setShowErrors] = useState(false);

  useEffect(() => {
    if (hours.data) {
      dispatch({ type: 'load', days: hours.data.days });
      setSaved(fullWeek(hours.data.days));
    }
  }, [hours.data]);

  const errors = weekErrors(days);
  const dirty = JSON.stringify(days) !== JSON.stringify(saved);

  async function submit() {
    setShowErrors(true);
    setSubmitError(null);
    if (Object.keys(errors).length) return;
    try {
      await save.mutateAsync(weekInput(days));
      setShowErrors(false);
    } catch (err) {
      setSubmitError(errorMessage(err));
    }
  }

  return (
    <section className="panel form-panel">
      <div className="panel-head">
        <div className="panel-title">Horário de funcionamento</div>
        {canEdit ? null : <span className="cell-muted">Somente leitura</span>}
      </div>

      {hours.isError ? (
        <div className="form-alert" role="alert">
          {errorMessage(hours.error)}{' '}
          <button type="button" className="btn btn-sm" onClick={() => void hours.refetch()}>
            Tentar de novo
          </button>
        </div>
      ) : null}
      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
        </div>
      ) : null}
      {hours.data?.warning && !dirty ? (
        <div className="form-warning" role="status">
          {hours.data.warning}
        </div>
      ) : null}

      <div className="panel-body">
        {hours.isPending ? (
          <span className="skeleton-bar" />
        ) : (
          <WeeklyHoursEditor
            days={days}
            onChange={(next) => dispatch({ type: 'edit', days: next })}
            errors={showErrors ? errors : {}}
            readOnly={!canEdit}
          />
        )}
        <p className="field-hint section-note">
          Mudar o horário não altera agendamentos já marcados; os que ficarem fora aparecem
          destacados na agenda.
        </p>
      </div>

      {canEdit ? (
        <div className="panel-foot">
          <button type="button" className="btn" disabled={!dirty || save.isPending} onClick={() => dispatch({ type: 'load', days: saved })}>
            Desfazer
          </button>
          <button type="button" className="btn-primary" disabled={!dirty || save.isPending} onClick={() => void submit()}>
            {save.isPending ? 'Salvando…' : 'Salvar horário'}
          </button>
        </div>
      ) : null}
    </section>
  );
}
