/** 45 → "45 min", 60 → "1 h", 90 → "1 h 30 min". */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) return `${rest} min`;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

/** Every duration a service may have: 5 min to 8 h, in steps of 5 (as the API requires). */
export const DURATION_OPTIONS: number[] = Array.from({ length: 96 }, (_, i) => (i + 1) * 5);
