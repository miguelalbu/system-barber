import { useEffect, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { ROLE_LABELS, useAuth, useMe, useUnitSelection } from '@/features/auth';
import { REGISTRY_PATH, visibleRegistries } from '@/features/registry';
import { initialsOf } from '@/shared/text/initials';
import Icon, { type IconName } from '@/shared/ui/Icon';

interface NavEntry {
  to: string;
  label: string;
  icon: IconName;
  badge?: string;
  /** Shown only to whoever has it (navigation by permission, S18). */
  permission?: string;
}

export const NAV: NavEntry[] = [
  { to: '/app/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/app/agenda', label: 'Agenda', icon: 'agenda' },
  { to: '/app/conversas', label: 'Conversas', icon: 'inbox', badge: '4' },
  { to: '/app/clientes', label: 'Clientes', icon: 'clientes' },
  { to: '/app/cadastros', label: 'Cadastros', icon: 'cadastros' },
  { to: '/app/financeiro', label: 'Financeiro', icon: 'financeiro' },
  { to: '/app/configuracoes', label: 'Configurações', icon: 'settings', permission: 'tenant:configure' },
  { to: '/app/tokens', label: 'Tokens', icon: 'tokens' },
];

export default function Sidebar() {
  const me = useMe();
  const { unitLabel, canSwitchUnit, cycleUnit } = useUnitSelection();
  const { signOut, can } = useAuth();
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
        {NAV.filter((item) => !item.permission || can(item.permission) !== null).map((item) =>
          item.to === REGISTRY_PATH ? (
            <RegistryNavGroup key={item.to} label={item.label} icon={item.icon} />
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
            </NavLink>
          ),
        )}
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

/**
 * "Cadastros" as a dropdown: the toggle opens the list of registries the user
 * may read, each a link to its own page. It starts open (and reopens) whenever
 * the current page is one of them.
 */
function RegistryNavGroup({ label, icon }: { label: string; icon: IconName }) {
  const { can } = useAuth();
  const { pathname } = useLocation();
  const inside = pathname === REGISTRY_PATH || pathname.startsWith(`${REGISTRY_PATH}/`);
  const [open, setOpen] = useState(inside);

  useEffect(() => {
    if (inside) setOpen(true);
  }, [inside]);

  const items = visibleRegistries(can);
  if (items.length === 0) return null;

  return (
    <div>
      <button
        type="button"
        className={`nav-item nav-group-toggle${inside ? ' is-current' : ''}`}
        aria-expanded={open}
        aria-controls="nav-registry"
        onClick={() => setOpen((o) => !o)}
      >
        <Icon name={icon} />
        <span>{label}</span>
        <Icon name="chevron-down" size={12} className={`nav-chevron${open ? ' is-open' : ''}`} />
      </button>
      {open ? (
        <ul id="nav-registry" className="nav-sub">
          {items.map((page) => (
            <li key={page.key}>
              <NavLink
                to={`${REGISTRY_PATH}/${page.key}`}
                className={({ isActive }) => `nav-sub-item${isActive ? ' is-active' : ''}`}
              >
                <Icon name={page.icon} size={14} />
                <span>{page.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
