import { NavLink } from 'react-router-dom';

const TABS = [
  { to: '/app/agenda', label: 'Agenda', end: true },
  { to: '/app/agenda/escala', label: 'Escala', end: false },
  { to: '/app/agenda/ausencias', label: 'Ausências', end: false },
];

/** Agenda · Escala · Ausências, shared by the three scheduling screens. */
export default function SchedulingTabs() {
  return (
    <nav className="tab-row" aria-label="Agenda">
      {TABS.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.end}
          className={({ isActive }) => `pill pill-lg${isActive ? ' is-active' : ''}`}
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}
