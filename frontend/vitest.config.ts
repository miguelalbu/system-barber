import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

// Reuses the Vite config (the `@/` alias above all). Tests live in tests/, at
// the repo root, not inside features (frontend DEC-004).
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      include: ['tests/**/*.test.ts'],
      environment: 'node',
    },
  }),
);
