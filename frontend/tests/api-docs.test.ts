import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { DOCS_DIR, extractCalls, normalizePath, renderAll } from '../scripts/api-docs';

describe('docs/api', () => {
  const { files, missing } = renderAll();

  it('every call the frontend makes exists in the backend contract', () => {
    expect(missing).toEqual([]);
  });

  it('is exactly what the generator produces (run `npm run docs:api`)', () => {
    const onDisk = Object.fromEntries(
      fs
        .readdirSync(DOCS_DIR)
        .filter((name) => name.endsWith('.md'))
        .map((name) => [name, fs.readFileSync(path.join(DOCS_DIR, name), 'utf8')]),
    );
    expect(onDisk).toEqual(files);
  });
});

describe('extractCalls', () => {
  it('reads method and path, defaulting to GET', () => {
    const source = `
      export function fetchMe() { return request<Me>('/auth/me'); }
      export async function remove(id: string) {
        return request<void>(\`/team/\${id}\`, { method: 'DELETE' });
      }`;
    expect(extractCalls(source, 'auth', 'x.ts')).toEqual([
      { feature: 'auth', file: 'x.ts', fn: 'fetchMe', method: 'GET', path: '/auth/me' },
      { feature: 'auth', file: 'x.ts', fn: 'remove', method: 'DELETE', path: '/team/${id}' },
    ]);
  });

  it('matches template literals with OpenAPI path parameters', () => {
    expect(normalizePath('/team/${userId}')).toBe(normalizePath('/team/{user_id}'));
  });
});
