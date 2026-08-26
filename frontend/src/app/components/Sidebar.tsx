import { NavLink } from 'react-router-dom';
import Icon, { type IconName } from './Icon';
import { CURRENT_USER, ORG_NAME, UNITS } from '@/data/app';

interface NavEntry {
  to: string;
  label: string;
  icon: IconName;
  badge?: string;
}

export const NAV: NavEntry[] = [
  { to: '/app/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/app/agenda', label: 'Agenda', icon: 'agenda' },
  { to: '/app/conversas', label: 'Conversas', icon: 'inbox', badge: '4' },
  { to: '/app/clientes', label: 'Clientes', icon: 'clientes' },
  { to: '/app/cadastros', label: 'Cadastros', icon: 'cadastros' },
  { to: '/app/financeiro', label: 'Financeiro', icon: 'financeiro' },
  { to: '/app/tokens', label: 'Tokens', icon: 'tokens' },
];

interface SidebarProps {
  unitIndex: number;
  onCycleUnit: () => void;
}

export default function Sidebar({ unitIndex, onCycleUnit }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark" />
        <span className="sidebar-brand-name">Navalha</span>
      </div>

      <div className="sidebar-unit">
        <div className="sidebar-org">{ORG_NAME}</div>
        <button type="button" className="unit-switch" onClick={onCycleUnit}>
          <span>{UNITS[unitIndex]}</span>
          <Icon name="chevron-down" size={12} stroke="var(--app-muted-2)" />
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
            {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-user">
        <div className="avatar avatar-sq">{CURRENT_USER.initials}</div>
        <div style={{ minWidth: 0 }}>
          <div className="sidebar-user-name">{CURRENT_USER.name}</div>
          <div className="sidebar-user-role">{CURRENT_USER.role}</div>
        </div>
      </div>
    </aside>
  );
}
