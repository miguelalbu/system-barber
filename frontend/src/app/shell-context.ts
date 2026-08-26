import { createContext, useContext } from 'react';
import type { ModalKind } from '@/types';

export interface ShellContextValue {
  /** Abre o modal de agendamento (origem IA ou manual). */
  openAppointment: (kind: ModalKind) => void;
  /** Unidade selecionada no seletor da sidebar. */
  unit: string;
}

export const ShellContext = createContext<ShellContextValue | null>(null);

export function useShell(): ShellContextValue {
  const ctx = useContext(ShellContext);
  if (!ctx) throw new Error('useShell precisa estar dentro de <AppLayout>');
  return ctx;
}
