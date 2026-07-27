import { defineConfig } from 'vitest/config'

export default defineConfig({
  root: 'packages/desktop',
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
