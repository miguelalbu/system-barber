/**
 * Tipos de domínio do painel.
 * Espelham o que o backend deverá expor — hoje alimentados pelos mocks
 * em `src/data/app.ts`, amanhã pelas funções de `src/api/client.ts`.
 */

export type AppointmentStatus = 'confirmado' | 'pendente' | 'concluido' | 'cancelado';
export type BadgeKind = AppointmentStatus | 'ativo';

export interface Barber {
  id: string;
  name: string;
  initials: string;
  /** Janela de trabalho no dia, ex.: "09:00–19:00". */
  shift: string;
}

export interface Appointment {
  id: string;
  barberId: string;
  /** "HH:MM" */
  start: string;
  /** "HH:MM" */
  end: string;
  client: string;
  service: string;
  status: AppointmentStatus;
  /** Criado pelo atendimento automatizado no WhatsApp. */
  fromAi?: boolean;
}

export interface UpcomingAppointment {
  id: string;
  time: string;
  client: string;
  service: string;
  barber: string;
  status: string;
  kind: BadgeKind;
}

export interface BarberOccupancy {
  name: string;
  pct: number;
}

export type ThreadTag = 'IA conduzindo' | 'Aguardando humano' | 'Resolvida';

export interface Thread {
  id: string;
  name: string;
  time: string;
  last: string;
  tag: ThreadTag;
  /** Selo extra, ex.: "Agendou" ou "Humano". */
  note?: string;
}

export interface Message {
  id: string;
  author: 'cliente' | 'ia' | 'humano';
  text: string;
  meta: string;
}

export interface ClientFact {
  label: string;
  value: string;
}

export interface ClientVisit {
  service: string;
  meta: string;
}

export interface BarberRecord {
  id: string;
  initials: string;
  name: string;
  email: string;
  unit: string;
  services: string;
  commission: string;
  hours: string;
  status: string;
  kind: BadgeKind;
}

export interface Kpi {
  label: string;
  value: string;
  hint: string;
}

/** Estados de demonstração da agenda enquanto não há backend. */
export type AgendaDemoState = 'normal' | 'vazio' | 'conflito';

export type ModalKind = 'ia' | 'manual';
