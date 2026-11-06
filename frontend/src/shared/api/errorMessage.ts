import { ApiError, NetworkError } from './http';

/**
 * What a form or list shows for a failed call. A 422 means the local
 * validation let something through that the API refused: point at the fields
 * instead of echoing a technical message.
 */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.status === 422 ? 'Confira os campos' : error.message;
  }
  if (error instanceof NetworkError) return error.message;
  return 'Algo deu errado. Tente de novo.';
}

/** The API's status for this error, if it came from the API. */
export function statusOf(error: unknown): number | null {
  return error instanceof ApiError ? error.status : null;
}
