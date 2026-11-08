/**
 * Wall-clock times as the API sends them ("HH:MM", no timezone) and as minutes
 * since midnight, which is easier to compare. Used by opening hours and,
 * later, by the agenda.
 */

/** "09:30" → 570. Accepts "H:MM" too; anything else → NaN. */
export function toMinutes(hhmm: string): number {
  const match = /^(\d{1,2}):(\d{2})$/.exec(hhmm.trim());
  if (!match) return Number.NaN;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (hours > 23 || minutes > 59) return Number.NaN;
  return hours * 60 + minutes;
}

/** 570 → "09:30". */
export function fromMinutes(total: number): string {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

/** Every 5 minutes of the day, "00:00" … "23:55": the options of a time select. */
export const FIVE_MINUTE_TIMES: string[] = Array.from({ length: 288 }, (_, i) => fromMinutes(i * 5));

/** "09:00–12:00". */
export function formatRange(opensAt: string, closesAt: string): string {
  return `${opensAt}–${closesAt}`;
}
