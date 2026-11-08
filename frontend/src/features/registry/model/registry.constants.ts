import type { IconName } from '@/shared/ui/Icon';

/**
 * The registries under "Cadastros", in menu order (PD-09, spec S05). Each has its
 * own page at `/app/cadastros/<key>` and an entry in the sidebar dropdown;
 * `permission` hides it from whoever cannot read it, and `ready: false` shows
 * the "em breve" page.
 */
export const REGISTRY_PAGES = [
  { key: 'unidades', label: 'Unidades', icon: 'unit', permission: null, ready: true },
  { key: 'barbeiros', label: 'Barbeiros', icon: 'scissors', permission: 'team:read', ready: true },
  { key: 'servicos', label: 'Serviços', icon: 'clock', permission: 'catalog:read', ready: true },
  { key: 'produtos', label: 'Produtos', icon: 'bottle', permission: 'catalog:read', ready: false },
  { key: 'combos', label: 'Combos', icon: 'layers', permission: 'catalog:read', ready: false },
  { key: 'clubes', label: 'Clubes', icon: 'star', permission: 'catalog:read', ready: false },
  { key: 'pacotes', label: 'Pacotes', icon: 'ticket', permission: 'catalog:read', ready: false },
  {
    key: 'formas-de-pagamento',
    label: 'Formas de pagamento',
    icon: 'card',
    permission: 'catalog:read',
    ready: false,
  },
] as const satisfies ReadonlyArray<{
  key: string;
  label: string;
  icon: IconName;
  permission: string | null;
  ready: boolean;
}>;

export type RegistryKey = (typeof REGISTRY_PAGES)[number]['key'];
export type RegistryPage = (typeof REGISTRY_PAGES)[number];

export const REGISTRY_PATH = '/app/cadastros';

/** The registry a key names, or undefined for an unknown key. */
export function registryPage(key: string | undefined): RegistryPage | undefined {
  return REGISTRY_PAGES.find((p) => p.key === key);
}

/** The registries a user may open, given `useAuth().can`. */
export function visibleRegistries(can: (permission: string) => unknown): RegistryPage[] {
  return REGISTRY_PAGES.filter((p) => p.permission === null || Boolean(can(p.permission)));
}

export const DEFAULT_COMMISSION = 40;
