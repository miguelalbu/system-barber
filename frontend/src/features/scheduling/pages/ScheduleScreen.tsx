import { useSearchParams } from 'react-router-dom';
import { useAuth, useMe, useUnitSelection } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import TableState from '@/shared/ui/TableState';
import { useBarberRefs, useSchedules } from '../api/schedule.queries';
import { WEEKDAYS, daySummary, formatWeeklyHours } from '../model/schedule.rules';
import SchedulingTabs from '../ui/SchedulingTabs';
import WeekEditor from './schedule/WeekEditor';

const COLUMNS = ['Barbeiro', ...WEEKDAYS.map((d) => d.short), 'Horas/semana'];

/** `/app/agenda/escala`: the weekly schedule of the active barbers, one row each. */
export default function ScheduleScreen() {
  const { can } = useAuth();
  const me = useMe();
  const { unitId } = useUnitSelection();
  const [params, setParams] = useSearchParams();
  const openId = params.get('barbeiro');
  const canEdit = can('team:manage') !== null;

  const schedules = useSchedules(unitId);
  const barbers = useBarberRefs(can('team:read') !== null);
  const nameOf = (id: string) =>
    barbers.data?.find((b) => b.id === id)?.name ?? (id === me.barber_id ? me.user.name : 'Barbeiro');
  const rows = [...(schedules.data ?? [])].sort((a, b) => nameOf(a.barber_id).localeCompare(nameOf(b.barber_id)));
  const opened = rows.find((r) => r.barber_id === openId) ?? null;

  function open(id: string | null) {
    const next = new URLSearchParams(params);
    if (id) next.set('barbeiro', id);
    else next.delete('barbeiro');
    setParams(next, { replace: true });
  }

  return (
    <div className="page-pad">
      <SchedulingTabs />
      <section className="panel">
        <table className="table schedule-grid">
          <thead>
            <tr>
              {COLUMNS.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {schedules.isPending ? <TableState columns={COLUMNS.length} state="loading" /> : null}
            {schedules.isError ? (
              <TableState
                columns={COLUMNS.length}
                state="error"
                message={errorMessage(schedules.error)}
                action={{ label: 'Tentar de novo', onClick: () => void schedules.refetch() }}
              />
            ) : null}
            {schedules.isSuccess && rows.length === 0 ? (
              <TableState columns={COLUMNS.length} state="empty" message="Nenhum barbeiro ativo nesta unidade." />
            ) : null}
            {rows.map((r) => (
              <tr
                key={r.barber_id}
                className={r.barber_id === openId ? 'is-selected is-clickable' : 'is-clickable'}
                onClick={() => open(r.barber_id)}
              >
                <td>
                  <div className="staff-name">{nameOf(r.barber_id)}</div>
                  {r.configured ? null : <span className="badge badge-concluido">Horário da unidade</span>}
                </td>
                {WEEKDAYS.map(({ weekday }) => {
                  const intervals = r.days.find((d) => d.weekday === weekday)?.intervals ?? [];
                  return (
                    <td key={weekday} className={`schedule-cell${intervals.length ? '' : ' is-off'}${r.configured ? '' : ' is-default'}`}>
                      {daySummary(intervals)}
                    </td>
                  );
                })}
                <td className="tnum">{formatWeeklyHours(r.weekly_minutes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {opened ? (
        <WeekEditor
          key={opened.barber_id}
          schedule={opened}
          barberName={nameOf(opened.barber_id)}
          canEdit={canEdit}
          onClose={() => open(null)}
        />
      ) : null}
    </div>
  );
}
