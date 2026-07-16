import { lazy, Suspense, useCallback, useState } from 'react'
import EditorShell from './components/EditorShell'
import ProjectHome from './components/ProjectHome'
import SettingsDialog, { type AppSettings } from './components/SettingsDialog'
import ToastRegion, { type ToastMessage } from './components/ToastRegion'

const DirectorModal = lazy(() => import('./components/director/DirectorModal'))

const settingsKey = 'sceneforge.settings'

function loadSettings(): AppSettings {
  try {
    const parsed = JSON.parse(localStorage.getItem(settingsKey) ?? '') as Partial<AppSettings>
    if ((parsed.generationMode === 'demo' || parsed.generationMode === 'api') && parsed.model) {
      return { generationMode: parsed.generationMode, model: parsed.model }
    }
  } catch {
    // Invalid local settings safely fall back to the demo mode.
  }
  return { generationMode: 'demo', model: 'demo-cinematic-v1' }
}

export default function App() {
  const [projectOpen, setProjectOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [directorOpen, setDirectorOpen] = useState(false)
  const [settings, setSettings] = useState<AppSettings>(loadSettings)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const addToast = useCallback(
    (message: string, tone: ToastMessage['tone'] = 'info') => {
      setToasts((current) => [...current, { id: Date.now() + current.length, message, tone }])
    },
    [],
  )

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const saveSettings = (next: AppSettings) => {
    setSettings(next)
    localStorage.setItem(settingsKey, JSON.stringify(next))
    setSettingsOpen(false)
    addToast(next.generationMode === 'demo' ? '已切换到本地演示模式。' : 'API 模式已启用。', 'success')
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        跳到主要内容
      </a>
      {projectOpen ? (
        <EditorShell
          settings={settings}
          onBack={() => setProjectOpen(false)}
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenDirector={() => setDirectorOpen(true)}
          onToast={addToast}
        />
      ) : (
        <ProjectHome onOpenProject={() => setProjectOpen(true)} />
      )}
      <SettingsDialog
        open={settingsOpen}
        settings={settings}
        onSave={saveSettings}
        onClose={() => setSettingsOpen(false)}
      />
      <Suspense fallback={null}>
        <DirectorModal
          open={directorOpen}
          onClose={() => setDirectorOpen(false)}
          onToast={addToast}
        />
      </Suspense>
      <ToastRegion toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}
