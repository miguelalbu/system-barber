/**
 * Demo data from the design prototype — not wired to the backend yet.
 * Replace with a `*.client.ts` + TanStack Query once the scheduling module exists
 * in the API (frontend DEC-005). Screens already consume the domain types, so
 * only this file changes.
 */
import type { Appointment, Barber } from '../model/scheduling.types';

/** The day shown in the prototype. */
export const AGENDA_DAY = 'Seg, 17 de agosto de 2026';

export const barbers: Barber[] = [
  { id: 'b1', name: 'Diego Martins', initials: 'DM', shift: '09:00–19:00' },
  { id: 'b2', name: 'Igor Salles', initials: 'IS', shift: '09:00–19:00' },
  { id: 'b3', name: 'Paulo Renato', initials: 'PR', shift: '08:00–17:00' },
  { id: 'b4', name: 'Vitor Hugo', initials: 'VH', shift: '12:00–20:00' },
];

export const appointments: Appointment[] = [
  { id: 'a1', barberId: 'b1', start: '08:30', end: '09:15', client: 'Rafael Lima', service: 'Corte + Barba', status: 'concluido', fromAi: true },
  { id: 'a2', barberId: 'b1', start: '09:30', end: '10:00', client: 'Bruno Tavares', service: 'Corte masculino', status: 'confirmado' },
  { id: 'a3', barberId: 'b1', start: '10:15', end: '11:00', client: 'Wesley Nunes', service: 'Corte + Barba', status: 'confirmado', fromAi: true },
  { id: 'a4', barberId: 'b1', start: '11:30', end: '12:00', client: 'Alan Prado', service: 'Barba', status: 'pendente' },
  { id: 'a5', barberId: 'b1', start: '14:00', end: '15:00', client: 'Cauã Ribeiro', service: 'Clube completo', status: 'confirmado' },
  { id: 'a6', barberId: 'b1', start: '16:00', end: '16:30', client: 'Otávio Serra', service: 'Corte masculino', status: 'confirmado', fromAi: true },
  { id: 'a7', barberId: 'b2', start: '09:00', end: '09:45', client: 'Marcelo Duarte', service: 'Corte + Barba', status: 'concluido' },
  { id: 'a8', barberId: 'b2', start: '10:00', end: '10:30', client: 'Felipe Andrade', service: 'Corte infantil', status: 'confirmado' },
  { id: 'a9', barberId: 'b2', start: '11:00', end: '11:45', client: 'Sérgio Vidal', service: 'Corte + Barba', status: 'cancelado' },
  { id: 'a10', barberId: 'b2', start: '13:30', end: '14:15', client: 'Rogério Pinto', service: 'Corte + Barba', status: 'confirmado', fromAi: true },
  { id: 'a11', barberId: 'b2', start: '15:30', end: '16:15', client: 'Danilo Cruz', service: 'Assinatura mensal', status: 'confirmado' },
  { id: 'a12', barberId: 'b2', start: '17:30', end: '18:00', client: 'Ivan Loureiro', service: 'Barba', status: 'pendente' },
  { id: 'a13', barberId: 'b3', start: '08:30', end: '09:00', client: 'Thiago Bastos', service: 'Corte masculino', status: 'concluido' },
  { id: 'a14', barberId: 'b3', start: '09:15', end: '10:15', client: 'Henrique Sá', service: 'Clube completo', status: 'concluido', fromAi: true },
  { id: 'a15', barberId: 'b3', start: '10:30', end: '11:15', client: 'Nelson Braga', service: 'Corte + Barba', status: 'confirmado' },
  { id: 'a16', barberId: 'b3', start: '12:00', end: '12:30', client: 'Lucas Ferraz', service: 'Barba', status: 'confirmado' },
  { id: 'a17', barberId: 'b3', start: '14:30', end: '15:30', client: 'Emerson Dias', service: 'Clube completo', status: 'confirmado', fromAi: true },
  { id: 'a18', barberId: 'b3', start: '18:00', end: '18:45', client: 'Ricardo Alcântara', service: 'Corte + Barba', status: 'pendente' },
  { id: 'a19', barberId: 'b4', start: '09:00', end: '09:30', client: 'Vinícius Mota', service: 'Corte masculino', status: 'concluido' },
  { id: 'a20', barberId: 'b4', start: '10:00', end: '11:00', client: 'André Quintela', service: 'Clube completo', status: 'confirmado' },
  { id: 'a21', barberId: 'b4', start: '11:15', end: '11:45', client: 'Joel Ramires', service: 'Corte infantil', status: 'confirmado', fromAi: true },
  { id: 'a22', barberId: 'b4', start: '13:00', end: '13:45', client: 'Murilo Tavares', service: 'Corte + Barba', status: 'confirmado' },
  { id: 'a23', barberId: 'b4', start: '15:00', end: '15:30', client: 'Pedro Zanetti', service: 'Barba', status: 'cancelado' },
  { id: 'a24', barberId: 'b4', start: '16:45', end: '17:30', client: 'Gustavo Peçanha', service: 'Corte + Barba', status: 'confirmado' },
];

export const serviceOptions = [
  'Corte + Barba — 45 min — R$ 85',
  'Corte masculino — 30 min — R$ 55',
];
