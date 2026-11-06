/**
 * Generate `docs/api/` — which backend endpoints each feature consumes.
 *
 *   npm run docs:api        (or `make docs-api` from the repo root; entry: api-docs.cli.ts)
 *
 * Source of truth on both sides, nothing typed by hand:
 *   - the calls: every `request<…>('/path', { method })` in src/features/<f>/api/*.api.ts,
 *     plus the transport itself (src/shared/api/*.ts — the token refresh lives there)
 *   - the contract: backend/tests/test_contracts/snapshots/openapi.json (the frozen API)
 *
 * A call to a route that is not in the contract is an error — the frontend
 * would be talking to an endpoint the backend does not serve.
 * tests/api-docs.test.ts fails when docs/api/ drifts from this output.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DOCS_DIR = path.join(ROOT, 'docs', 'api');
const FEATURES_DIR = path.join(ROOT, 'src', 'features');
const CONTRACT = path.resolve(ROOT, '..', 'backend', 'tests', 'test_contracts', 'snapshots', 'openapi.json');
const BACKEND_DOCS = '../../../backend/docs/api';

const HEADER =
  '<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api ' +
  'e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->';

interface Call {
  feature: string;
  file: string;
  fn: string;
  method: string;
  path: string;
}

interface Operation {
  tags?: string[];
  summary?: string;
  requestBody?: { content?: Record<string, { schema?: Schema }> };
  responses?: Record<string, { content?: Record<string, { schema?: Schema }> }>;
}

interface Schema {
  $ref?: string;
  type?: string;
  items?: Schema;
}

type Contract = { paths: Record<string, Record<string, Operation>> };

/** GitHub's heading anchor — the same rule as backend/tools/api_docs.py. */
export function anchor(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}_\s-]/gu, '')
    .trim()
    .replace(/\s/g, '-');
}

/** `/team/${userId}` → `/team/{}` and `/team/{user_id}` → `/team/{}`, so both sides compare. */
export function normalizePath(p: string): string {
  return p.replace(/\$\{[^}]+\}/g, '{}').replace(/\{[^}]+\}/g, '{}');
}

/** Every function that calls `request(...)` with a literal path, with its method and path. */
export function extractCalls(source: string, feature: string, file: string): Call[] {
  const calls: Call[] = [];
  const parts = source.split(/(?:export\s+)?(?:async\s+)?function\s+(\w+)/);
  for (let i = 1; i < parts.length; i += 2) {
    const fn = parts[i];
    const body = parts[i + 1];
    const call = body.match(/request(?:<[\s\S]*?>)?\(\s*(['`])([^'`]+)\1\s*(?:,\s*\{([\s\S]*?)\})?/);
    if (!call) continue;
    const method = call[3]?.match(/method:\s*['"](\w+)['"]/)?.[1] ?? 'GET';
    calls.push({ feature, file, fn, method: method.toUpperCase(), path: call[2] });
  }
  return calls;
}

const SHARED_API_DIR = path.join(ROOT, 'src', 'shared', 'api');
const SHARED = 'shared';

function readCalls(): Call[] {
  const calls: Call[] = [];
  for (const file of fs.readdirSync(SHARED_API_DIR).sort()) {
    if (!file.endsWith('.ts')) continue;
    const source = fs.readFileSync(path.join(SHARED_API_DIR, file), 'utf8');
    calls.push(...extractCalls(source, SHARED, `src/shared/api/${file}`));
  }
  for (const feature of fs.readdirSync(FEATURES_DIR).sort()) {
    const apiDir = path.join(FEATURES_DIR, feature, 'api');
    if (!fs.existsSync(apiDir)) continue;
    for (const file of fs.readdirSync(apiDir).sort()) {
      if (!file.endsWith('.api.ts')) continue;
      const source = fs.readFileSync(path.join(apiDir, file), 'utf8');
      calls.push(...extractCalls(source, feature, `src/features/${feature}/api/${file}`));
    }
  }
  return calls;
}

function schemaName(schema: Schema | undefined): string {
  if (!schema) return '—';
  if (schema.$ref) return `\`${schema.$ref.split('/').pop()}\``;
  if (schema.type === 'array') return `${schemaName(schema.items)}[]`;
  return schema.type ? `\`${schema.type}\`` : '—';
}

function findOperation(contract: Contract, call: Call): { path: string; op: Operation } | null {
  for (const [contractPath, ops] of Object.entries(contract.paths)) {
    if (normalizePath(contractPath) !== normalizePath(call.path)) continue;
    const op = ops[call.method.toLowerCase()];
    if (op) return { path: contractPath, op };
  }
  return null;
}

export function renderAll(): { files: Record<string, string>; missing: Call[] } {
  const contract = JSON.parse(fs.readFileSync(CONTRACT, 'utf8')) as Contract;
  const calls = readCalls();
  const missing: Call[] = [];
  const byFeature = new Map<string, string[]>();

  for (const call of calls) {
    const found = findOperation(contract, call);
    if (!found) {
      missing.push(call);
      continue;
    }
    const { path: contractPath, op } = found;
    const tag = op.tags?.[0] ?? 'infra';
    const link = `${BACKEND_DOCS}/${tag}.md#${anchor(`${call.method.toLowerCase()} ${contractPath}`)}`;
    const ok = Object.keys(op.responses ?? {}).find((s) => s.startsWith('2'));
    const response = ok ? schemaName(op.responses?.[ok]?.content?.['application/json']?.schema) : '—';
    const body = schemaName(op.requestBody?.content?.['application/json']?.schema);
    const row =
      `| \`${call.fn}()\` | [\`${call.method} ${contractPath}\`](${link}) | ${body} | ` +
      `${ok ? `\`${ok}\` ` : ''}${response} | ${op.summary ?? ''} |`;
    byFeature.set(call.feature, [...(byFeature.get(call.feature) ?? []), row]);
  }

  const files: Record<string, string> = {};
  const index: string[] = [];
  for (const [feature, rows] of [...byFeature.entries()].sort()) {
    const sources = [...new Set(calls.filter((c) => c.feature === feature).map((c) => c.file))];
    files[`${feature}.md`] = [
      HEADER,
      '',
      feature === SHARED ? '# Transporte compartilhado (`shared/api`)' : `# Feature \`${feature}\``,
      '',
      `Chamadas à API feitas em ${sources.map((s) => `\`${s}\``).join(', ')}. ` +
        'Campos, erros e regras de acesso de cada rota estão na referência do backend (links).',
      '',
      '| Função | Rota | Corpo | Resposta | Resumo |',
      '|---|---|---|---|---|',
      ...rows,
      '',
    ].join('\n');
    index.push(`| [\`${feature}\`](${feature}.md) | ${rows.length} |`);
  }

  const mocked = fs
    .readdirSync(FEATURES_DIR)
    .filter((f) => fs.existsSync(path.join(FEATURES_DIR, f, 'api')))
    .filter((f) => fs.readdirSync(path.join(FEATURES_DIR, f, 'api')).some((n) => n.endsWith('.mock.ts')))
    .sort();

  files['README.md'] = [
    HEADER,
    '',
    '# API consumida pelo frontend',
    '',
    'Quais endpoints do backend cada feature chama, casados com o contrato congelado ' +
      '(`backend/tests/test_contracts/snapshots/openapi.json`). A referência completa — campos, ' +
      'erros, permissões — está em [`backend/docs/api/`](../../../backend/docs/api/README.md).',
    '',
    '| Feature | Chamadas |',
    '|---|---|',
    ...index,
    '',
    '## Ainda sobre dados de demonstração',
    '',
    'Features com `api/*.mock.ts` (sem módulo no backend ainda): ' +
      (mocked.length ? mocked.map((f) => `\`${f}\``).join(', ') : 'nenhuma') +
      '.',
    '',
    'Todas as chamadas passam por `src/shared/api/http.ts` (base `/api`, `X-Tenant-Slug` em dev, ' +
      'bearer e renovação de token).',
    '',
  ].join('\n');

  return { files, missing };
}

export function main(): number {
  const { files, missing } = renderAll();
  if (missing.length) {
    for (const call of missing) {
      console.error(`✗ ${call.file}: ${call.fn}() chama ${call.method} ${call.path}, que não está no contrato`);
    }
    return 1;
  }
  fs.mkdirSync(DOCS_DIR, { recursive: true });
  for (const [name, content] of Object.entries(files)) {
    fs.writeFileSync(path.join(DOCS_DIR, name), content, 'utf8');
  }
  for (const name of fs.readdirSync(DOCS_DIR)) {
    if (name.endsWith('.md') && !(name in files)) fs.unlinkSync(path.join(DOCS_DIR, name));
  }
  console.log(`docs/api: ${Object.keys(files).length} arquivos`);
  return 0;
}
