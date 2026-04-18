import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    maxWorkers: 2,
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    setupFiles: [],
    exclude: ['tests/smoke/**/*.spec.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
