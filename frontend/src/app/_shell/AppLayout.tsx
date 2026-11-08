import { Outlet, useLocation } from 'react-router-dom';
import { UnitSelectionProvider } from '@/features/auth';
import { REGISTRY_PATH, registryPage } from '@/features/registry';
import { AppointmentModalProvider } from '@/features/scheduling';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import '@/shared/styles/panel.css';

const TITLES: Record<string, string> = {
  '/app/dashboard': 'Dashboard',
  '/app/agenda': 'Agenda',
  '/app/agenda/escala': 'Agenda · Escala',
  '/app/agenda/ausencias': 'Agenda · Ausências',
  '/app/conversas': 'Central de conversas',
  '/app/clientes': 'Clientes',
  '/app/cadastros': 'Cadastros',
  '/app/financeiro': 'Financeiro',
  '/app/configuracoes': 'Configurações',
  '/app/tokens': 'Sistema de tokens',
};

/** Title of the top bar; each registry page reads "Cadastros · <registry>". */
function titleOf(pathname: string): string {
  if (pathname.startsWith(`${REGISTRY_PATH}/`)) {
    const page = registryPage(pathname.slice(REGISTRY_PATH.length + 1));
    if (page) return `Cadastros · ${page.label}`;
  }
  return TITLES[pathname] ?? 'Navalha';
}

/** The authenticated panel: sidebar, top bar and the active screen. */
export default function AppLayout() {
  const { pathname } = useLocation();

  return (
    <UnitSelectionProvider>
      <div className="app-shell">
        {/* Inside .app-shell, so the booking modal inherits the panel tokens. */}
        <AppointmentModalProvider>
          <Sidebar />

          <main className="app-main">
            <Topbar title={titleOf(pathname)} />
            <div className="app-content">
              <Outlet />
            </div>
          </main>
        </AppointmentModalProvider>
      </div>
    </UnitSelectionProvider>
  );
}
