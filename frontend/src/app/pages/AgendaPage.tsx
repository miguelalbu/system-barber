import { useMemo, useState } from 'react';
import Icon from '../components/Icon';
import { AGENDA_DAY, appointments, barbers } from '@/data/app';
import type { AgendaDemoState, Appointment, AppointmentStatus } from '@/types';
import { useShell } from '../shell-context';

/** Altura de uma hora, em pixels. */
const ROW = 88;
const DAY_START = 8;
const DAY_END = 20;
const NOW = '10:42';

const toMinutes = (time: string) => {
  const [h, m] = time.split(':').map(Number);
  return h * 60 + m;
};

const HOURS = Array.from({ length: DAY_END - DAY_START + 1 }, (_, i) =>
  `${String(DAY_START + i).padStart(2, '0')}:00`,
);

const VIEWS = ['Dia', 'Semana', 'Mês'];

const FILTERS = [
  { key: 'Barbeiro:', value: 'todos' },
  { key: 'Serviço:', value: 'todos' },
  { key: 'Status:', value: '3 de 4' },
];

const DEMO_STATES: Array<{ id: AgendaDemoState; label: string }> = [
  { id: 'normal', label: 'Dia cheio' },
  { id: 'vazio', label: 'Dia vazio' },
  { id: 'conflito', label: 'Conflito' },
];

const LEGEND: Array<{ label: string; status: AppointmentStatus }> = [
  { label: 'Confirmado', status: 'confirmado' },
  { label: 'Pendente', status: 'pendente' },
  { label: 'Concluído', status: 'concluido' },
  { label: 'Cancelado', status: 'cancelado' },
];

function geometry(appointment: Appointment) {
  const start = toMinutes(appointment.start);
  const duration = toMinutes(appointment.end) - start;
  return {
    top: ((start - DAY_START * 60) / 60) * ROW,
    height: (duration / 60) * ROW - 3,
    compact: duration <= 30,
  };
}

export default function AgendaPage() {
  const { openAppointment } = useShell();
  const [demo, setDemo] = useState<AgendaDemoState>('normal');
  const [view, setView] = useState('Dia');
  const [showAiTags, setShowAiTags] = useState(true);

  const isEmpty = demo === 'vazio';

  const byBarber = useMemo(() => {
    if (isEmpty) return barbers.map(() => [] as Appointment[]);
    return barbers.map((b) => appointments.filter((a) => a.barberId === b.id));
  }, [isEmpty]);

  const nowTop = ((toMinutes(NOW) - DAY_START * 60) / 60) * ROW;

  return (
    <div className="agenda">
      <div className="agenda-toolbar">
        <div className="stepper">
          <button type="button" className="stepper-arrow" aria-label="Dia anterior">
            <Icon name="chevron-left" size={13} />
          </button>
          <button type="button" className="stepper-today">
            Hoje
          </button>
          <button type="button" className="stepper-arrow" aria-label="Próximo dia">
            <Icon name="chevron-right" size={13} />
          </button>
        </div>

        <div className="agenda-date">{AGENDA_DAY}</div>

        <div className="segmented">
          {VIEWS.map((v) => (
            <button
              type="button"
              key={v}
              className={`seg seg-wide${view === v ? ' is-active' : ''}`}
              onClick={() => setView(v)}
            >
              {v}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8, marginLeft: 8 }}>
          {FILTERS.map((f) => (
            <button type="button" className="filter-button" key={f.key}>
              <span className="filter-key">{f.key}</span>
              <span className="filter-value">{f.value}</span>
              <Icon name="chevron-down" size={11} stroke="var(--app-muted-2)" />
            </button>
          ))}
        </div>

        <div className="toolbar-right">
          <button
            type="button"
            className={`pill${showAiTags ? ' is-active' : ''}`}
            onClick={() => setShowAiTags((v) => !v)}
            title="Mostrar o selo IA nos atendimentos criados pelo WhatsApp"
          >
            Selo IA
          </button>

          <div className="segmented">
            <span className="segmented-label">Demo</span>
            {DEMO_STATES.map((d) => (
              <button
                type="button"
                key={d.id}
                className={`seg${demo === d.id ? ' is-active' : ''}`}
                onClick={() => setDemo(d.id)}
              >
                {d.label}
              </button>
            ))}
          </div>

          <button type="button" className="btn-primary" onClick={() => openAppointment('manual')}>
            Novo agendamento
          </button>
        </div>
      </div>

      {demo === 'conflito' ? (
        <div className="conflict">
          <Icon name="warning" stroke="#A0483A" style={{ marginTop: 1 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="conflict-title">
              Conflito de horário: Diego Martins já tem atendimento às 10:30
            </div>
            <div className="conflict-body">
              O agendamento de Rafael Lima (Corte + Barba, 45 min) invade o atendimento de Bruno
              Tavares, que termina às 11:00. Escolha outro horário, outro barbeiro, ou reduza a
              duração do serviço.
            </div>
            <div className="conflict-actions">
              <button type="button" className="conflict-btn">
                Ver próximo horário livre (11:00)
              </button>
              <button type="button" className="conflict-btn">
                Trocar barbeiro
              </button>
              <button type="button" className="conflict-dismiss" onClick={() => setDemo('normal')}>
                Descartar
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="agenda-scroll">
        <div className="agenda-grid" style={{ '--agenda-columns': barbers.length } as React.CSSProperties}>
          <div className="agenda-corner" />
          {barbers.map((b) => (
            <div className="agenda-colhead" key={b.id}>
              <div className="avatar avatar-sm">{b.initials}</div>
              <div style={{ minWidth: 0 }}>
                <div className="agenda-colhead-name truncate">{b.name}</div>
                <div className="agenda-colhead-meta">{b.shift}</div>
              </div>
            </div>
          ))}

          <div className="agenda-gutter">
            {HOURS.map((h) => (
              <div className="agenda-hour" key={h}>
                <span>{h}</span>
              </div>
            ))}
          </div>

          {barbers.map((barber, index) => (
            <div className="agenda-col" key={barber.id}>
              {HOURS.map((h) => (
                <div className="agenda-slot" key={h} />
              ))}

              {index === 0 && !isEmpty ? (
                <div className="agenda-now" style={{ top: nowTop }} />
              ) : null}

              {byBarber[index].map((appointment) => {
                const { top, height, compact } = geometry(appointment);
                return (
                  <button
                    type="button"
                    key={appointment.id}
                    className={`event is-${appointment.status}${compact ? ' is-compact' : ''}`}
                    style={{ top, height }}
                    onClick={() => openAppointment(appointment.fromAi ? 'ia' : 'manual')}
                  >
                    <div className="event-head">
                      <span className="event-range">
                        {appointment.start}–{appointment.end}
                      </span>
                      {appointment.fromAi && showAiTags ? (
                        <span className="event-ai">IA</span>
                      ) : null}
                    </div>
                    <div className="event-client">{appointment.client}</div>
                    {!compact ? <div className="event-service">{appointment.service}</div> : null}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {isEmpty ? (
          <div className="agenda-empty">
            <div className="agenda-empty-card">
              <div className="agenda-empty-title">Nenhum agendamento em 17 de agosto</div>
              <div className="agenda-empty-body">
                A unidade Centro está aberta das 08:00 às 20:00 com 4 barbeiros escalados. Você pode
                agendar manualmente ou liberar os horários para o atendimento por WhatsApp.
              </div>
              <div className="agenda-empty-actions">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => openAppointment('manual')}
                >
                  Novo agendamento
                </button>
                <button type="button" className="btn">
                  Editar escala do dia
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="agenda-legend">
        {LEGEND.map((l) => (
          <div className="legend-item" key={l.status}>
            <span className={`legend-swatch is-${l.status}`} />
            <span>{l.label}</span>
          </div>
        ))}
        <span style={{ marginLeft: 'auto' }}>Arraste um atendimento para reagendar</span>
      </div>
    </div>
  );
}
