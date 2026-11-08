/** Server state of the settings screen (TanStack Query). */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/features/auth';
import type { ShopSettingsUpdate } from '../model/settings.types';
import * as api from './settings.api';

export const settingsKeys = { shop: ['settings', 'shop'] as const };

export function useShopSettings() {
  return useQuery({ queryKey: settingsKeys.shop, queryFn: api.getShopSettings });
}

export function useSaveShopSettings() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: ShopSettingsUpdate) => api.updateShopSettings(input),
    onSuccess: (saved) => client.setQueryData(settingsKeys.shop, saved),
  });
}

/** Renaming shows in the sidebar, which reads `/auth/me`. */
export function useRenameShop() {
  const { reloadMe } = useAuth();
  return useMutation({
    mutationFn: api.renameShop,
    onSuccess: () => reloadMe().catch(() => undefined),
  });
}
