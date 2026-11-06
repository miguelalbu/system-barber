import { describe, expect, it } from 'vitest';
import { ALL_UNITS_LABEL, unitLabelsFor } from '@/features/auth/model/unitSelection';

const unit = (name: string) => ({ id: name, name, timezone: 'America/Sao_Paulo', active: true });

describe('unitLabelsFor', () => {
  it('adds the aggregate option for someone who sees several units', () => {
    expect(unitLabelsFor({ all_units: true, units: [unit('Centro'), unit('Zona Sul')] })).toEqual([
      'Centro',
      'Zona Sul',
      ALL_UNITS_LABEL,
    ]);
  });

  it('has nothing to switch in a single-unit shop', () => {
    expect(unitLabelsFor({ all_units: true, units: [unit('Centro')] })).toEqual(['Centro']);
  });

  it('never offers the aggregate to someone scoped to some units', () => {
    expect(unitLabelsFor({ all_units: false, units: [unit('Centro'), unit('Zona Sul')] })).toEqual([
      'Centro',
      'Zona Sul',
    ]);
  });
});
