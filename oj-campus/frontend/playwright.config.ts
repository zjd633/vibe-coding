import { defineConfig } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const databasePath = path.join(root, 'backend', 'data', 'playwright-e2e.db')
const databaseUrl = `sqlite:///${databasePath.replaceAll('\\', '/')}`
const python = path.join(root, 'backend', '.venv', 'Scripts', 'python.exe')
const browserCache = path.join(process.env.LOCALAPPDATA ?? '', 'ms-playwright')
const downloadedChromium = fs.existsSync(browserCache)
  ? fs.readdirSync(browserCache).filter((entry) => entry.startsWith('chromium-')).sort().reverse()
    .map((entry) => path.join(browserCache, entry, 'chrome-win64', 'chrome.exe')).find(fs.existsSync)
  : undefined
export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure', launchOptions: downloadedChromium ? { executablePath: downloadedChromium } : undefined },
  webServer: [
    { command: 'node e2e/start-api.mjs', cwd: root + '/frontend', env: { ...process.env, OJ_DATABASE_URL: databaseUrl }, url: 'http://127.0.0.1:8000/api/problems', timeout: 30_000, reuseExistingServer: false },
    { command: `"${python}" -m app.worker`, cwd: path.join(root, 'backend'), env: { ...process.env, OJ_DATABASE_URL: databaseUrl }, timeout: 30_000, reuseExistingServer: false },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5173', cwd: root + '/frontend', url: 'http://127.0.0.1:5173', timeout: 30_000, reuseExistingServer: false },
  ],
})
