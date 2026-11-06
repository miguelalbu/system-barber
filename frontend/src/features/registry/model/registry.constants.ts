/** Tabs of "Cadastros"; the key goes in the URL (`?aba=`). */
export const REGISTRY_TABS = [
  { key: 'unidades', label: 'Unidades' },
  { key: 'barbeiros', label: 'Barbeiros' },
  { key: 'servicos', label: 'Serviços' },
  { key: 'clubes', label: 'Clubes e combos' },
  { key: 'planos', label: 'Planos' },
] as const;

export type RegistryTab = (typeof REGISTRY_TABS)[number]['key'];

export const DEFAULT_COMMISSION = 40;
