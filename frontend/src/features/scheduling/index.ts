/** Public API of the scheduling feature — the only entry point other code may import. */
export { default as AgendaScreen } from './pages/AgendaScreen';
export { default as ScheduleScreen } from './pages/ScheduleScreen';
export { default as TimeOffScreen } from './pages/TimeOffScreen';
export { AppointmentModalProvider, useAppointmentModal } from './model/appointmentModal';
export type { AppointmentOrigin } from './model/scheduling.types';
