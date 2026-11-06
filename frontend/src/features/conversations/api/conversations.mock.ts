/**
 * Demo data from the design prototype — not wired to the backend yet.
 * Replace with a `*.client.ts` + TanStack Query once the conversations module exists
 * in the API (frontend DEC-005). Screens already consume the domain types, so
 * only this file changes.
 */
import type { ClientFact, ClientVisit, Message, Thread } from '../model/conversations.types';

export const threads: Thread[] = [
  { id: 't1', name: 'Rafael Lima', time: '09:41', last: 'Perfeito, pode marcar 10:30 com o Diego', tag: 'IA conduzindo', note: 'Agendou' },
  { id: 't2', name: 'Sérgio Vidal', time: '09:22', last: 'Preciso desmarcar hoje, deu um imprevisto', tag: 'Aguardando humano' },
  { id: 't3', name: 'Danilo Cruz', time: '08:57', last: 'Quanto fica o plano mensal com barba?', tag: 'IA conduzindo' },
  { id: 't4', name: 'Alan Prado', time: 'Ontem', last: 'Confirmado, obrigado!', tag: 'Resolvida' },
  { id: 't5', name: 'Ivan Loureiro', time: 'Ontem', last: 'Vocês atendem sábado à tarde?', tag: 'IA conduzindo' },
  { id: 't6', name: 'Emerson Dias', time: '15/08', last: 'Assumida por Camila · encerrada', tag: 'Resolvida', note: 'Humano' },
];

export const messages: Message[] = [
  { id: 'm1', author: 'cliente', text: 'Oi, tem horário hoje pra corte e barba?', meta: 'Cliente · 09:36' },
  { id: 'm2', author: 'ia', text: 'Oi, Rafael. Hoje temos 10:30 com o Diego e 14:00 com o Igor. Corte + Barba leva 45 min, R$ 85.', meta: 'IA · 09:37' },
  { id: 'm3', author: 'cliente', text: 'Perfeito, pode marcar 10:30 com o Diego', meta: 'Cliente · 09:41' },
  { id: 'm4', author: 'ia', text: 'Agendado para hoje às 10:30 com Diego Martins. Vou te lembrar 2 horas antes.', meta: 'IA · 09:41' },
];

export const quickReplies = ['Confirmar presença', 'Oferecer outro horário', 'Enviar tabela de preços'];

export const clientFacts: ClientFact[] = [
  { label: 'Telefone', value: '+55 11 98812-4417' },
  { label: 'Unidade', value: 'Centro' },
  { label: 'Barbeiro habitual', value: 'Diego Martins' },
  { label: 'Plano', value: 'Clube Barba + Cabelo' },
  { label: 'Ticket médio', value: 'R$ 82' },
  { label: 'Faltas', value: '1 em 14 visitas' },
];

export const clientHistory: ClientVisit[] = [
  { service: 'Corte + Barba', meta: '02/08 · Diego Martins · R$ 85' },
  { service: 'Corte masculino', meta: '19/07 · Diego Martins · R$ 55' },
  { service: 'Corte + Barba', meta: '05/07 · Igor Salles · R$ 85' },
];
