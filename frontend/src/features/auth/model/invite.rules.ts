/** Rules of the invite acceptance form. The backend repeats them; these guide the user. */

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;

/** The problem with the chosen password, or null when it can be sent. */
export function passwordProblem(password: string, confirmation: string): string | null {
  if (password.length < PASSWORD_MIN) {
    return `A senha precisa de pelo menos ${PASSWORD_MIN} caracteres.`;
  }
  if (password.length > PASSWORD_MAX) {
    return `A senha pode ter no máximo ${PASSWORD_MAX} caracteres.`;
  }
  if (password !== password.trim()) {
    // A pasted password with a trailing space is the classic "right password, 401" (ISS-006).
    return 'A senha não pode começar nem terminar com espaço.';
  }
  if (password !== confirmation) {
    return 'As duas senhas não conferem.';
  }
  return null;
}

/** The token is the last path segment of the invite link (`/convite/<token>`). */
export function tokenFromPath(token: string | undefined): string | null {
  const value = token?.trim();
  return value ? value : null;
}
