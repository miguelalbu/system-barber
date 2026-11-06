import type { BadgeVariant } from '@/shared/ui/Badge';

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
  kind: BadgeVariant;
}
