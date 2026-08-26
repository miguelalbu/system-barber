/**
 * Dados de demonstração do painel, extraídos do protótipo de design.
 * Substitua por chamadas de `src/api/client.ts` quando o backend existir.
 */
import type {
  Appointment,
  Barber,
  BarberOccupancy,
  BarberRecord,
  ClientFact,
  ClientVisit,
  Kpi,
  Message,
  Thread,
  UpcomingAppointment,
} from '@/types';

export const UNITS = ['Unidade Centro', 'Unidade Zona Sul', 'Todas as unidades'];

export const CURRENT_USER = { name: 'Camila Rocha', role: 'Recepção', initials: 'CR' };

export const ORG_NAME = 'Barbearia Central';

/** Dia exibido no protótipo. */
export const AGENDA_DAY = 'Seg, 17 de agosto de 2026';
export const DASHBOARD_DAY = 'Segunda, 17 de agosto';

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

export const serviceOptions = [
  'Corte + Barba — 45 min — R$ 85',
  'Corte masculino — 30 min — R$ 55',
];
