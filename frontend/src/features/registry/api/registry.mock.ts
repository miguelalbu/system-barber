/**
 * Demo data from the design prototype — not wired to the backend yet.
 * Replace with a `*.client.ts` + TanStack Query once the catalog module exists
 * in the API (frontend DEC-005). Screens already consume the domain types, so
 * only this file changes.
 */
import type { BarberRecord } from '../model/registry.types';

export const cadastroTabs = ['Unidades', 'Barbeiros', 'Serviços', 'Clubes e combos', 'Planos'];

export const barberRecords: BarberRecord[] = [
  { id: 'r1', initials: 'DM', name: 'Diego Martins', email: 'diego@barbeariacentral.com.br', unit: 'Centro', services: 'Corte, Barba, Clube completo', commission: '45%', hours: '48h', status: 'Ativo', kind: 'ativo' },
  { id: 'r2', initials: 'IS', name: 'Igor Salles', email: 'igor@barbeariacentral.com.br', unit: 'Centro', services: 'Corte, Barba, Infantil', commission: '40%', hours: '44h', status: 'Ativo', kind: 'ativo' },
  { id: 'r3', initials: 'PR', name: 'Paulo Renato', email: 'paulo@barbeariacentral.com.br', unit: 'Centro', services: 'Corte, Barba', commission: '42%', hours: '40h', status: 'Ativo', kind: 'ativo' },
  { id: 'r4', initials: 'VH', name: 'Vitor Hugo', email: 'vitor@barbeariacentral.com.br', unit: 'Zona Sul', services: 'Corte, Clube completo, Infantil', commission: '38%', hours: '36h', status: 'Ativo', kind: 'ativo' },
  { id: 'r5', initials: 'LC', name: 'Leandro Cotrim', email: 'leandro@barbeariacentral.com.br', unit: 'Zona Sul', services: 'Corte, Barba', commission: '40%', hours: '32h', status: 'Férias', kind: 'pendente' },
  { id: 'r6', initials: 'MF', name: 'Mateus Fialho', email: 'mateus@barbeariacentral.com.br', unit: 'Zona Sul', services: 'Corte', commission: '35%', hours: '—', status: 'Inativo', kind: 'concluido' },
];

export const serviceChips: Array<{ label: string; enabled: boolean }> = [
  { label: 'Corte masculino', enabled: true },
  { label: 'Barba', enabled: true },
  { label: 'Corte + Barba', enabled: true },
  { label: 'Clube completo', enabled: true },
  { label: 'Corte infantil', enabled: false },
  { label: 'Pigmentação', enabled: false },
];
