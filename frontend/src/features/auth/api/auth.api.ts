/** Authentication endpoints. These are live — no mocks behind them. */

import { request } from '@/shared/api/http';
import type { Me } from '../model/auth.types';

interface TokensResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(email: string, password: string) {
  const tokens = await request<TokensResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
    anonymous: true,
  });
  return { accessToken: tokens.access_token, refreshToken: tokens.refresh_token };
}

export function fetchMe() {
  return request<Me>('/auth/me');
}

export function logout(refreshToken: string) {
  return request<void>('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    anonymous: true,
  });
}
