import { useCallback, useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import AppointmentModal from './components/AppointmentModal';
import { ShellContext } from './shell-context';
import { useMe } from '@/auth/AuthContext';
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

const ALL_UNITS = 'Todas as unidades';

export default function AppLayout() {
  const { pathname } = useLocation();
  const me = useMe();
  const [unitIndex, setUnitIndex] = useState(0);
  const [modal, setModal] = useState<ModalKind | null>(null);

  // Real units from /auth/me. Someone who sees every unit also gets the
  // aggregate option; someone scoped to one unit has nothing to switch.
  const unitLabels = useMemo(() => {
    const names = me.units.map((unit) => unit.name);
    return me.all_units && names.length > 1 ? [...names, ALL_UNITS] : names;
  }, [me.units, me.all_units]);

  const unitLabel = unitLabels[unitIndex] ?? unitLabels[0] ?? 'Sem unidade';
  const canSwitchUnit = unitLabels.length > 1;

  const openAppointment = useCallback((kind: ModalKind) => setModal(kind), []);
  const cycleUnit = useCallback(() => {
    setUnitIndex((index) => (index + 1) % unitLabels.length);
  }, [unitLabels.length]);

  const shell = useMemo(
    () => ({ openAppointment, unit: unitLabel }),
    [openAppointment, unitLabel],
  );

  return (
    <ShellContext.Provider value={shell}>
      <div className="app-shell">
        <Sidebar
          unitLabel={unitLabel}
          canSwitchUnit={canSwitchUnit}
          onCycleUnit={cycleUnit}
        />

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
