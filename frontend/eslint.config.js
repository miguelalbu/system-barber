// ESLint flat config. Besides the usual TS/React checks, it enforces the
// dependency direction of the feature architecture (frontend/.github/rules.md):
//
//   app      → features, shared
//   features → shared, and another feature ONLY through its index.ts
//   shared   → nothing above it
//
// The feature zones are generated from the folders in src/features, so a new
// feature is covered without touching this file.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import js from '@eslint/js';
import importPlugin from 'eslint-plugin-import';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';
import tseslint from 'typescript-eslint';

const root = path.dirname(fileURLToPath(import.meta.url));
const featuresDir = path.join(root, 'src/features');
const features = fs
  .readdirSync(featuresDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

const featureZones = features.map((feature) => ({
  target: `./src/features/${feature}`,
  from: './src/features',
  // Its own folder, plus every other feature's public barrel.
  except: [`./${feature}`, ...features.filter((f) => f !== feature).map((f) => `./${f}/index.ts`)],
  message: 'Uma feature só importa outra pelo index.ts dela (rules.md, "Architecture").',
}));

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}', 'tests/**/*.ts'],
    languageOptions: { globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, import: importPlugin },
    settings: {
      'import/resolver': { typescript: { project: './tsconfig.json' } },
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'import/no-restricted-paths': [
        'error',
        {
          zones: [
            {
              target: './src/shared',
              from: ['./src/features', './src/app'],
              message: 'shared/ não conhece features nem o app (rules.md, "Architecture").',
            },
            {
              target: './src/features',
              from: './src/app',
              message: 'Uma feature não importa o app/; o app é quem compõe as features.',
            },
            ...featureZones,
          ],
        },
      ],
      // No legacy top-level folders: a file belongs to a feature or to shared/.
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/components/*', '@/hooks/*', '@/lib/*', '@/utils/*', '@/types', '@/data/*', '@/api/*', '@/auth/*'],
              message: 'Pasta de topo herdada: o arquivo pertence a uma feature ou a shared/.',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['*.config.{js,ts}'],
    languageOptions: { globals: globals.node },
  },
);
