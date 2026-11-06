const BRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

/** 4550 → "R$ 45,50". The API keeps money in integer cents. */
export function formatBRL(cents: number): string {
  return BRL.format(cents / 100);
}

/** What a price field shows for a value in cents: 4550 → "45,50". */
export function centsToInput(cents: number): string {
  return (cents / 100).toFixed(2).replace('.', ',');
}

/**
 * A typed price in reais to cents, or null when it is not a valid amount.
 * Accepts "45", "45,5", "45,50", "R$ 1.234,56" and "45.50".
 */
export function parseBRL(text: string): number | null {
  let clean = text.replace(/R\$/i, '').replace(/\s/g, '');
  if (!clean) return null;
  if (clean.includes(',')) clean = clean.replace(/\./g, '').replace(',', '.');
  if (!/^\d+(\.\d{1,2})?$/.test(clean)) return null;
  return Math.round(Number(clean) * 100);
}
