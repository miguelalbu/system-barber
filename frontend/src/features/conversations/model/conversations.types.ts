/** WhatsApp conversations handled by the assistant or by a person. */

export type ThreadTag = 'IA conduzindo' | 'Aguardando humano' | 'Resolvida';

export interface Thread {
  id: string;
  name: string;
  time: string;
  last: string;
  tag: ThreadTag;
  /** Extra tag, e.g. "Agendou" or "Humano". */
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
