/** Shop settings (`/tenant/settings`): public contact and booking policies. */

export interface ShopSettings {
  /** E.164. */
  contact_phone: string | null;
  instagram: string | null;
  about: string | null;
  min_advance_minutes: number;
  max_advance_days: number;
  confirmation_deadline_hours: number;
  client_change_min_hours: number;
  late_tolerance_minutes: number;
  max_future_appointments_per_client: number;
  barber_sees_client_contact: boolean;
  updated_at: string;
}

export type ShopSettingsUpdate = Partial<Omit<ShopSettings, 'updated_at'>>;

export type SettingsSection = 'barbearia' | 'agendamento';
