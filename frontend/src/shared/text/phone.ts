/**
 * Phone numbers as the panel shows and accepts them. The API stores E.164
 * (`+5511987654321`) and normalizes whatever is typed; these mirror its rule
 * (backend `app/modules/clients/phone.py`) so the form can warn first.
 */

const digitsOf = (text: string) => text.replace(/\D/g, '');

/** "+5511987654321" → "(11) 98765-4321"; a foreign number stays as stored. */
export function formatPhone(e164: string): string {
  const match = /^\+55(\d{2})(\d{4,5})(\d{4})$/.exec(e164);
  return match ? `(${match[1]}) ${match[2]}-${match[3]}` : e164;
}

/** Same acceptance rule as the API: BR with area code, or `+` and 8–15 digits. */
export function isValidPhone(text: string): boolean {
  const trimmed = text.trim();
  const digits = digitsOf(trimmed);
  if (trimmed.startsWith('+')) return digits.length >= 8 && digits.length <= 15;
  if (digits.length === 10 || digits.length === 11) return true;
  return (digits.length === 12 || digits.length === 13) && digits.startsWith('55');
}

/** Progressive Brazilian mask while typing: "1198765" → "(11) 98765". `+…` is left alone. */
export function maskPhone(text: string): string {
  if (text.trim().startsWith('+')) return text;
  const d = digitsOf(text).slice(0, 11);
  if (d.length <= 2) return d.length ? `(${d}` : '';
  const local = d.slice(2);
  const split = d.length === 11 ? 5 : 4;
  if (local.length <= split) return `(${d.slice(0, 2)}) ${local}`;
  return `(${d.slice(0, 2)}) ${local.slice(0, split)}-${local.slice(split)}`;
}
