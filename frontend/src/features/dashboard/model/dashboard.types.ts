import type { BadgeVariant } from '@/shared/ui/Badge';

export interface Kpi {
  label: string;
  value: string;
  hint: string;
}

export interface UpcomingAppointment {
  id: string;
  time: string;
  client: string;
  service: string;
  barber: string;
  status: string;
  kind: BadgeVariant;
}

export interface BarberOccupancy {
  name: string;
  pct: number;
}
