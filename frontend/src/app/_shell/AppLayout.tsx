import { Outlet, useLocation } from 'react-router-dom';
import { UnitSelectionProvider } from '@/features/auth';
import { AppointmentModalProvider } from '@/features/scheduling';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import '@/shared/styles/panel.css';

const TITLES: Record<string, string> = {
  '/app/dashboard': 'Dashboard',
  '/app/agenda': 'Agenda',
  '/app/conversas': 'Central de conversas',
  '/app/clientes': 'Clientes',
  '/app/cadastros': 'Cadastros · Barbeiros',
  '/app/financeiro': 'Financeiro',
  '/app/tokens': 'Sistema de tokens',
};

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
            <Topbar title={TITLES[pathname] ?? 'Navalha'} />
            <div className="app-content">
              <Outlet />
            </div>
          </main>
        </AppointmentModalProvider>
      </div>
    </UnitSelectionProvider>
  );
}
