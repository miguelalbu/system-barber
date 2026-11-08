import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth, useUnitSelection } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import TableState from '@/shared/ui/TableState';
import { useBarberRefs, useDeleteTimeOff, useTimeOff } from '../api/schedule.queries';
import { TIME_OFF_LABELS, addDays, periodLabel } from '../model/schedule.rules';
import type { AffectedAppointment, TimeOff } from '../model/schedule.types';
import { localToday } from '../model/today';
import SchedulingTabs from '../ui/SchedulingTabs';
import TimeOffForm from './time-off/TimeOffForm';

const COLUMNS = ['Barbeiro', 'Tipo', 'Período', 'Motivo', ''];

/** `/app/agenda/ausencias`: whole-day absences (blocks live in the agenda itself). */
export default function TimeOffScreen() {
  const { can } = useAuth();
  const { unitId } = useUnitSelection();
  const [params, setParams] = useSearchParams();
  const showPast = params.get('passadas') === '1';
  const canEdit = can('team:manage') !== null;
  const today = localToday();
  const from = showPast ? addDays(today, -365) : today;
  const to = addDays(from, 365);

  const timeOff = useTimeOff(unitId, from, to);
  const barbers = useBarberRefs(can('team:read') !== null);
  const remove = useDeleteTimeOff();
  const [editing, setEditing] = useState<TimeOff | 'new' | null>(null);
  const [deleting, setDeleting] = useState<TimeOff | null>(null);
  const [notice, setNotice] = useState<{ affected: AffectedAppointment[]; name: string } | null>(null);

  const nameOf = (id: string) => barbers.data?.find((b) => b.id === id)?.name ?? 'Barbeiro';
  const rows = (timeOff.data ?? []).filter((t) => t.all_day);
  const activeBarbers = (barbers.data ?? []).filter((b) => b.active && (unitId === null || b.unit_id === unitId));

  return (
    <div className="page-pad">
      <SchedulingTabs />
      <section className="panel">
        <div className="toolbar">
          <label className="check-field">
            <input
              type="checkbox"
              checked={showPast}
              onChange={(e) => setParams(e.target.checked ? { passadas: '1' } : {}, { replace: true })}
            />
            Mostrar passadas
          </label>
          <div className="toolbar-end">
            {timeOff.data ? <span className="record-count">{rows.length} registros</span> : null}
            {canEdit ? (
              <button type="button" className="btn-primary" onClick={() => setEditing('new')} disabled={!activeBarbers.length}>
                Nova ausência
              </button>
            ) : null}
          </div>
        </div>

        {notice?.affected.length ? (
          <div className="form-warning" role="status">
            {notice.affected.length} agendamento{notice.affected.length > 1 ? 's' : ''} de {notice.name} nesse período
            continua{notice.affected.length > 1 ? 'm' : ''} marcado{notice.affected.length > 1 ? 's' : ''}.
          </div>
        ) : null}

        <table className="table">
          <thead>
            <tr>
              {COLUMNS.map((c, i) => (
                <th key={c || 'actions'} className={i === COLUMNS.length - 1 ? 'col-right' : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timeOff.isPending ? <TableState columns={COLUMNS.length} state="loading" /> : null}
            {timeOff.isError ? (
              <TableState
                columns={COLUMNS.length}
                state="error"
                message={errorMessage(timeOff.error)}
                action={{ label: 'Tentar de novo', onClick: () => void timeOff.refetch() }}
              />
            ) : null}
            {timeOff.isSuccess && rows.length === 0 ? (
              <TableState
                columns={COLUMNS.length}
                state="empty"
                message={showPast ? 'Nenhuma ausência no último ano nem à frente.' : 'Nenhuma folga, férias ou atestado marcado.'}
              />
            ) : null}
            {rows.map((t) => (
              <tr key={t.id}>
                <td className="staff-name">{nameOf(t.barber_id)}</td>
                <td>{TIME_OFF_LABELS[t.kind]}</td>
                <td className="tnum">{periodLabel(t.starts_on, t.ends_on)}</td>
                <td className="cell-muted">{t.reason ?? '—'}</td>
                <td className="col-right">
                  {canEdit ? (
                    <span className="row-actions">
                      {t.ends_on >= today ? (
                        <button type="button" className="btn btn-sm" onClick={() => setEditing(t)}>
                          Editar
                        </button>
                      ) : null}
                      <button type="button" className="btn btn-sm" onClick={() => setDeleting(t)}>
                        Apagar
                      </button>
                    </span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {editing ? (
        <TimeOffForm
          key={editing === 'new' ? 'new' : editing.id}
          timeOff={editing === 'new' ? null : editing}
          barbers={editing === 'new' ? activeBarbers : barbers.data ?? []}
          onClose={() => setEditing(null)}
          onSaved={(affected, name) => {
            setNotice({ affected, name });
            setEditing(null);
          }}
        />
      ) : null}

      {deleting ? (
        <ConfirmDialog
          title="Apagar esta ausência?"
          confirmLabel="Apagar"
          danger
          busy={remove.isPending}
          error={remove.error ? errorMessage(remove.error) : null}
          onConfirm={() => void remove.mutateAsync(deleting.id).then(() => setDeleting(null))}
          onCancel={() => setDeleting(null)}
        >
          <p>
            {TIME_OFF_LABELS[deleting.kind]} de {nameOf(deleting.barber_id)} ({periodLabel(deleting.starts_on, deleting.ends_on)}).
            Os dias voltam a seguir a escala.
          </p>
        </ConfirmDialog>
      ) : null}
    </div>
  );
}
