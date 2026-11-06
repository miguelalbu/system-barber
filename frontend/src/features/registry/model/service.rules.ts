import { centsToInput, parseBRL } from '@/shared/text/money';
import type { Service, ServiceInput } from './registry.types';

export interface ServiceForm {
  name: string;
  description: string;
  duration: number;
  price: string;
  active: boolean;
}

export type ServiceErrors = Partial<Record<'name' | 'description' | 'price', string>>;

export const MAX_PRICE_CENTS = 10_000_000;

export function emptyServiceForm(): ServiceForm {
  return { name: '', description: '', duration: 30, price: '', active: true };
}

export function serviceToForm(service: Service): ServiceForm {
  return {
    name: service.name,
    description: service.description ?? '',
    duration: service.duration_minutes,
    price: centsToInput(service.price_cents),
    active: service.active,
  };
}

/** Same limits as the API (`ServiceIn`). */
export function validateService(form: ServiceForm): ServiceErrors {
  const errors: ServiceErrors = {};
  const name = form.name.trim();
  if (name.length < 2) errors.name = 'Informe o nome (mínimo 2 letras)';
  else if (name.length > 80) errors.name = 'Nome muito longo (máximo 80)';
  if (form.description.trim().length > 500) errors.description = 'Máximo de 500 caracteres';
  const cents = parseBRL(form.price);
  if (cents === null) errors.price = 'Informe o preço, ex.: 45,00';
  else if (cents > MAX_PRICE_CENTS) errors.price = 'Preço acima do limite';
  return errors;
}

export function serviceInput(form: ServiceForm): ServiceInput {
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    duration_minutes: form.duration,
    price_cents: parseBRL(form.price) ?? 0,
    active: form.active,
  };
}
