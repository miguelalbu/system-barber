import { NavLink, useNavigate } from 'react-router-dom';
import { ROLE_LABELS, useAuth, useMe, useUnitSelection } from '@/features/auth';
import { initialsOf } from '@/shared/text/initials';
import Icon, { type IconName } from '@/shared/ui/Icon';

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

export default function Sidebar() {
  const me = useMe();
  const { unitLabel, canSwitchUnit, cycleUnit } = useUnitSelection();
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
          onClick={cycleUnit}
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
