import { execFileSync, spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const root = path.resolve(frontend, '..')
const database = path.join(root, 'backend', 'data', 'playwright-e2e.db')
const databaseUrl = process.env.OJ_DATABASE_URL ?? `sqlite:///${database.replaceAll('\\', '/')}`
const python = path.join(root, 'backend', '.venv', 'Scripts', 'python.exe')

// This launcher runs before the API listens, so E2E never shares the demo DB.
for (const suffix of ['', '-wal', '-shm']) fs.rmSync(database + suffix, { force: true })
execFileSync(python, ['-m', 'app.seed'], { cwd: path.join(root, 'backend'), env: { ...process.env, OJ_DATABASE_URL: databaseUrl }, stdio: 'inherit' })
const child = spawn(python, ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8000'], {
  cwd: path.join(root, 'backend'), env: { ...process.env, OJ_DATABASE_URL: databaseUrl }, stdio: 'inherit',
})
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal))
child.on('exit', (code) => process.exit(code ?? 1))
