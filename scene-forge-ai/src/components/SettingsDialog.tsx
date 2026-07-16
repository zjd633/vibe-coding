import { useEffect, useState } from 'react'
import { KeyRound, Server, ShieldCheck, X } from 'lucide-react'

export interface AppSettings {
  generationMode: 'demo' | 'api'
  model: string
}

interface SettingsDialogProps {
  open: boolean
  settings: AppSettings
  onSave: (settings: AppSettings) => void
  onClose: () => void
}

export default function SettingsDialog({
  open,
  settings,
  onSave,
  onClose,
}: SettingsDialogProps) {
  const [draft, setDraft] = useState(settings)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setDraft(settings)
    setError('')
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose, open, settings])

  if (!open) return null

  const save = () => {
    const model = draft.model.trim()
    if (!model) {
      setError('模型名称不能为空。')
      return
    }
    onSave({ ...draft, model })
  }

  return (
    <div className="dialog-scrim">
      <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <header>
          <div className="settings-icon" aria-hidden="true">
            <Server size={19} />
          </div>
          <div>
            <p>GENERATION PROVIDER</p>
            <h2 id="settings-title">生成设置</h2>
          </div>
          <button className="icon-button" type="button" aria-label="关闭设置" onClick={onClose}>
            <X size={19} />
          </button>
        </header>

        <div className="settings-body">
          <label className="settings-field">
            <span>生成模式</span>
            <select
              aria-label="生成模式"
              value={draft.generationMode}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  generationMode: event.target.value as AppSettings['generationMode'],
                }))
              }
            >
              <option value="demo">本地演示模式（无需密钥）</option>
              <option value="api">OpenAI-compatible API</option>
            </select>
            <small>演示模式会生成稳定的本地 SVG 镜头，不发送网络请求。</small>
          </label>

          <label className="settings-field">
            <span>模型名称</span>
            <input
              aria-label="模型名称"
              value={draft.model}
              onChange={(event) => setDraft((current) => ({ ...current, model: event.target.value }))}
              autoComplete="off"
            />
            <small>API 模式下会原样传给本地代理。</small>
          </label>

          {error && (
            <p className="settings-error" role="alert">
              {error}
            </p>
          )}

          <div className="settings-security-note">
            <ShieldCheck size={19} aria-hidden="true" />
            <div>
              <strong>密钥只放服务端</strong>
              <p>
                浏览器不会保存 API Key。请复制 <code>.env.example</code> 的变量到启动环境中。
              </p>
            </div>
          </div>

          <div className="settings-endpoint-preview">
            <KeyRound size={16} aria-hidden="true" />
            <span>请求路径</span>
            <code>/api/generate</code>
          </div>
        </div>

        <footer>
          <button className="secondary-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="primary-button" type="button" onClick={save}>
            保存设置
          </button>
        </footer>
      </section>
    </div>
  )
}
