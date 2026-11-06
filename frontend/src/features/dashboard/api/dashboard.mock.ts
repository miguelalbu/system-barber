/**
 * Demo data from the design prototype — not wired to the backend yet.
 * Replace with a `*.client.ts` + TanStack Query once the reporting module exists
 * in the API (frontend DEC-005). Screens already consume the domain types, so
 * only this file changes.
 */
import type { BarberOccupancy, Kpi, UpcomingAppointment } from '../model/dashboard.types';

export const DASHBOARD_DAY = 'Segunda, 17 de agosto';

export const dashboardKpis: Kpi[] = [
  { label: 'Agendamentos hoje', value: '38', hint: '6 pendentes de confirmação' },
  { label: 'Ocupação média', value: '78%', hint: '4 barbeiros escalados' },
  { label: 'Faltas evitadas', value: '9', hint: 'Confirmações por lembrete (7 dias)' },
  { label: 'Receita prevista', value: 'R$ 2.940', hint: 'R$ 1.180 já em comanda' },
];

export const upcoming: UpcomingAppointment[] = [
  { id: 'u1', time: '10:15', client: 'Wesley Nunes', service: 'Corte + Barba', barber: 'Diego Martins', status: 'Confirmado', kind: 'confirmado' },
  { id: 'u2', time: '10:30', client: 'Nelson Braga', service: 'Corte + Barba', barber: 'Paulo Renato', status: 'Confirmado', kind: 'confirmado' },
  { id: 'u3', time: '11:00', client: 'André Quintela', service: 'Clube completo', barber: 'Vitor Hugo', status: 'Confirmado', kind: 'confirmado' },
  { id: 'u4', time: '11:15', client: 'Joel Ramires', service: 'Corte infantil', barber: 'Vitor Hugo', status: 'Confirmado', kind: 'confirmado' },
  { id: 'u5', time: '11:30', client: 'Alan Prado', service: 'Barba', barber: 'Diego Martins', status: 'Pendente', kind: 'pendente' },
  { id: 'u6', time: '12:00', client: 'Lucas Ferraz', service: 'Barba', barber: 'Paulo Renato', status: 'Confirmado', kind: 'confirmado' },
  { id: 'u7', time: '13:00', client: 'Murilo Tavares', service: 'Corte + Barba', barber: 'Vitor Hugo', status: 'Confirmado', kind: 'confirmado' },
];

export const occupancy: BarberOccupancy[] = [
  { name: 'Diego Martins', pct: 86 },
  { name: 'Igor Salles', pct: 74 },
  { name: 'Paulo Renato', pct: 81 },
  { name: 'Vitor Hugo', pct: 69 },
];
