import { NavLink, useNavigate } from 'react-router-dom';
import Icon, { type IconName } from './Icon';
import { ROLE_LABELS } from '@/api/auth';
import { useAuth, useMe } from '@/auth/AuthContext';

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

/** "Miguel Albuquerque" → "MA". Matches how the panel renders every avatar. */
export function initialsOf(name: string): string {
  const parts = name.split(' ').filter(Boolean);
  if (parts.length === 0) return '??';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

interface SidebarProps {
  unitLabel: string;
  canSwitchUnit: boolean;
  onCycleUnit: () => void;
}

export default function Sidebar({ unitLabel, canSwitchUnit, onCycleUnit }: SidebarProps) {
  const me = useMe();
  const { signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate('/entrar', { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark" />
        <span className="sidebar-brand-name">Navalha</span>
      </div>

      <div className="sidebar-unit">
        <div className="sidebar-org">{me.tenant.name}</div>
        <button
          type="button"
          className="unit-switch"
          onClick={onCycleUnit}
          disabled={!canSwitchUnit}
          // A single unit has nothing to switch to, so the control stays inert.
          title={canSwitchUnit ? 'Trocar de unidade' : undefined}
        >
          <span>{unitLabel}</span>
          {canSwitchUnit ? (
            <Icon name="chevron-down" size={12} stroke="var(--app-muted-2)" />
          ) : null}
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
        <div className="avatar avatar-sq">{initialsOf(me.user.name)}</div>
        <div style={{ minWidth: 0 }}>
          <div className="sidebar-user-name">{me.user.name}</div>
          <div className="sidebar-user-role">{ROLE_LABELS[me.user.role]}</div>
        </div>
        <button
          type="button"
          className="sidebar-signout"
          onClick={handleSignOut}
          aria-label="Sair"
          title="Sair"
        >
          <Icon name="logout" size={14} />
        </button>
      </div>
    </aside>
  );
}
