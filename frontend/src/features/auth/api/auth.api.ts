/** Authentication endpoints. These are live — no mocks behind them. */

import { request } from '@/shared/api/http';
import type { InviteLookup, Me } from '../model/auth.types';

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

/** Describe an invite without using it — so the screen can refuse a dead link up front. */
export function lookupInvite(token: string) {
  return request<InviteLookup>('/team/invites/lookup', {
    method: 'POST',
    body: { token },
    anonymous: true,
  });
}

/** Create the login from an invite (team invite or the owner's first access). */
export function acceptInvite(token: string, password: string) {
  return request<{ id: string; email: string }>('/team/invites/accept', {
    method: 'POST',
    body: { token, password },
    anonymous: true,
  });
}
