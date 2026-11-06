import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { AppointmentModal } from '../ui/AppointmentModal';
import type { AppointmentOrigin } from './scheduling.types';

interface AppointmentModalValue {
  /** Open the booking modal, prefilled by the assistant or empty for the front desk. */
  openAppointment: (origin: AppointmentOrigin) => void;
}

const AppointmentModalContext = createContext<AppointmentModalValue | null>(null);

/**
 * Owns the booking modal for the whole panel: any screen can open it, and it
 * renders next to `children` — inside the shell, so it inherits its tokens.
 */
export function AppointmentModalProvider({ children }: { children: React.ReactNode }) {
  const [origin, setOrigin] = useState<AppointmentOrigin | null>(null);

  const openAppointment = useCallback((next: AppointmentOrigin) => setOrigin(next), []);
  const close = useCallback(() => setOrigin(null), []);
  const value = useMemo(() => ({ openAppointment }), [openAppointment]);

  return (
    <AppointmentModalContext.Provider value={value}>
      {children}
      {origin ? <AppointmentModal kind={origin} onClose={close} /> : null}
    </AppointmentModalContext.Provider>
  );
}

export function useAppointmentModal(): AppointmentModalValue {
  const ctx = useContext(AppointmentModalContext);
  if (!ctx) throw new Error('useAppointmentModal precisa estar dentro de <AppointmentModalProvider>');
  return ctx;
}
