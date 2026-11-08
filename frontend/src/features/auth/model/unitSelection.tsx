import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { useMe } from './authContext';
import type { Me } from './auth.types';

export const ALL_UNITS_LABEL = 'Todas as unidades';

/**
 * Options of the unit switcher, from the real units in `/auth/me`. Someone who
 * sees every unit also gets the aggregate option; someone scoped to one unit
 * has nothing to switch.
 */
export function unitLabelsFor(me: Pick<Me, 'units' | 'all_units'>): string[] {
  const names = me.units.map((unit) => unit.name);
  return me.all_units && names.length > 1 ? [...names, ALL_UNITS_LABEL] : names;
}

/** Options of the switcher with their unit ids (`null` = every unit, the aggregate option). */
export function unitOptionsFor(me: Pick<Me, 'units' | 'all_units'>): { id: string | null; label: string }[] {
  const options: { id: string | null; label: string }[] = me.units.map((u) => ({ id: u.id, label: u.name }));
  return me.all_units && options.length > 1 ? [...options, { id: null, label: ALL_UNITS_LABEL }] : options;
}

interface UnitSelectionValue {
  /** Unit picked in the sidebar switcher. */
  unitLabel: string;
  /** Its id; `null` when "Todas as unidades" (or no unit) is picked. */
  unitId: string | null;
  canSwitchUnit: boolean;
  cycleUnit: () => void;
}

const UnitSelectionContext = createContext<UnitSelectionValue | null>(null);

export function UnitSelectionProvider({ children }: { children: React.ReactNode }) {
  const me = useMe();
  const [unitIndex, setUnitIndex] = useState(0);

  const options = useMemo(() => unitOptionsFor(me), [me]);
  const unitLabels = useMemo(() => options.map((o) => o.label), [options]);

  const cycleUnit = useCallback(() => {
    setUnitIndex((index) => (index + 1) % unitLabels.length);
  }, [unitLabels.length]);

  const value = useMemo(
    () => ({
      unitLabel: unitLabels[unitIndex] ?? unitLabels[0] ?? 'Sem unidade',
      unitId: (options[unitIndex] ?? options[0])?.id ?? null,
      canSwitchUnit: unitLabels.length > 1,
      cycleUnit,
    }),
    [options, unitLabels, unitIndex, cycleUnit],
  );

  return <UnitSelectionContext.Provider value={value}>{children}</UnitSelectionContext.Provider>;
}

export function useUnitSelection(): UnitSelectionValue {
  const ctx = useContext(UnitSelectionContext);
  if (!ctx) throw new Error('useUnitSelection precisa estar dentro de <UnitSelectionProvider>');
  return ctx;
}
