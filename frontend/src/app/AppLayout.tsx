import { useCallback, useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import AppointmentModal from './components/AppointmentModal';
import { ShellContext } from './shell-context';
import { UNITS } from '@/data/app';
import type { ModalKind } from '@/types';
import './app.css';

const TITLES: Record<string, string> = {
  '/app/dashboard': 'Dashboard',
  '/app/agenda': 'Agenda',
  '/app/conversas': 'Central de conversas',
  '/app/clientes': 'Clientes',
  '/app/cadastros': 'Cadastros · Barbeiros',
  '/app/financeiro': 'Financeiro',
  '/app/tokens': 'Sistema de tokens',
};

export default function AppLayout() {
  const { pathname } = useLocation();
  const [unitIndex, setUnitIndex] = useState(0);
  const [modal, setModal] = useState<ModalKind | null>(null);

  const openAppointment = useCallback((kind: ModalKind) => setModal(kind), []);
  const cycleUnit = useCallback(() => setUnitIndex((i) => (i + 1) % UNITS.length), []);

  const shell = useMemo(
    () => ({ openAppointment, unit: UNITS[unitIndex] }),
    [openAppointment, unitIndex],
  );

  return (
    <ShellContext.Provider value={shell}>
      <div className="app-shell">
        <Sidebar unitIndex={unitIndex} onCycleUnit={cycleUnit} />

        <main className="app-main">
          <Topbar title={TITLES[pathname] ?? 'Navalha'} />
          <div className="app-content">
            <Outlet />
          </div>
        </main>

        {modal ? <AppointmentModal kind={modal} onClose={() => setModal(null)} /> : null}
      </div>
    </ShellContext.Provider>
  );
}
