/** Shop settings and the shop's name (identity, spec S01). */

import { request } from '@/shared/api/http';
import type { ShopSettings, ShopSettingsUpdate } from '../model/settings.types';

export function getShopSettings() {
  return request<ShopSettings>('/tenant/settings');
}

export function updateShopSettings(input: ShopSettingsUpdate) {
  return request<ShopSettings>('/tenant/settings', { method: 'PATCH', body: input });
}

/** The shop's display name lives in the control plane (`PATCH /tenant`). */
export function renameShop(name: string) {
  return request<{ name: string }>('/tenant', { method: 'PATCH', body: { name } });
}
