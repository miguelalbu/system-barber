import { Link } from 'react-router-dom';
import { Badge, Tag } from '../components/Badge';
import { DASHBOARD_DAY, dashboardKpis, occupancy, threads, upcoming } from '@/data/app';
import { useShell } from '../shell-context';

export default function DashboardPage() {
  const { unit } = useShell();
  const waiting = threads.filter((t) => t.tag !== 'Resolvida').slice(0, 3);

  return (
    <div className="page-pad">
      <div className="day-head">
        <div className="day-title">{DASHBOARD_DAY}</div>
        <div className="day-meta">Atualizado às 08:12 · {unit}</div>
      </div>

      <div className="kpi-grid">
        {dashboardKpis.map((kpi) => (
          <div className="kpi" key={kpi.label}>
            <div className="kpi-label">{kpi.label}</div>
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-hint">{kpi.hint}</div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-head">
            <div className="panel-title">Próximos agendamentos</div>
            <Link to="/app/agenda" className="btn-link">
              Ver agenda
            </Link>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 68 }}>Hora</th>
                <th>Cliente</th>
                <th>Serviço</th>
                <th>Barbeiro</th>
                <th style={{ width: 132 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {upcoming.map((row) => (
                <tr key={row.id}>
                  <td className="tnum" style={{ fontWeight: 500 }}>
                    {row.time}
                  </td>
                  <td>{row.client}</td>
                  <td className="cell-muted">{row.service}</td>
                  <td className="cell-muted">{row.barber}</td>
                  <td>
                    <Badge kind={row.kind}>{row.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <div className="stack-16">
          <section className="panel">
            <div className="panel-head">
              <div className="panel-title">Ocupação por barbeiro</div>
            </div>
            <div className="occupancy-list">
              {occupancy.map((b) => (
                <div className="occupancy-row" key={b.name}>
                  <div className="occupancy-head">
                    <span>{b.name}</span>
                    <span className="tnum cell-muted">{b.pct}%</span>
                  </div>
                  <div className="occupancy-track">
                    <div className="occupancy-bar" style={{ width: `${b.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <div className="panel-title">Conversas aguardando</div>
              <Link to="/app/conversas" className="btn-link">
                Abrir central
              </Link>
            </div>
            <div className="waiting-list">
              {waiting.map((w) => (
                <div className="waiting-row" key={w.id}>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div className="waiting-name">{w.name}</div>
                    <div className="cell-muted truncate">{w.last}</div>
                  </div>
                  <Tag tag={w.tag} label={w.tag === 'Aguardando humano' ? 'Aguardando' : 'IA'} />
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
