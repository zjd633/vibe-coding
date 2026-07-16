import { ArrowLeft, Box, Film, Image, Settings, Sparkles, Video } from 'lucide-react'
import type { AppSettings } from './SettingsDialog'
import WorkflowCanvas from './WorkflowCanvas'

interface EditorShellProps {
  settings: AppSettings
  onBack: () => void
  onOpenSettings: () => void
  onOpenDirector: () => void
  onToast: (message: string, tone?: 'success' | 'error' | 'info') => void
}

export default function EditorShell({
  settings,
  onBack,
  onOpenSettings,
  onOpenDirector,
  onToast,
}: EditorShellProps) {
  return (
    <div className="editor-page">
      <header className="editor-header">
        <div className="editor-header-leading">
          <button
            className="icon-button"
            type="button"
            aria-label="返回项目管理"
            onClick={onBack}
          >
            <ArrowLeft size={19} aria-hidden="true" />
          </button>
          <span className="editor-brand" aria-hidden="true">
            <Sparkles size={18} />
          </span>
          <div>
            <p className="editor-kicker">SCENEFORGE / PROJECT</p>
            <h1>庭院漫剧</h1>
          </div>
        </div>
        <div className="editor-header-actions">
          <span className="save-status">
            <span className="save-dot" /> 已自动保存
          </span>
          <span className={`mode-badge mode-${settings.generationMode}`}>
            {settings.generationMode === 'demo' ? 'DEMO' : 'API'}
          </span>
          <button className="icon-button" type="button" aria-label="打开设置" onClick={onOpenSettings}>
            <Settings size={19} aria-hidden="true" />
          </button>
        </div>
      </header>
      <main id="main-content" className="editor-main" aria-label="节点编辑器">
        <aside className="canvas-toolbar" aria-label="节点工具">
          <button type="button" aria-label="图片节点">
            <Image size={17} />
            <span>图片</span>
          </button>
          <button type="button" aria-label="3D 节点" onClick={onOpenDirector}>
            <Box size={17} />
            <span>3D</span>
          </button>
          <button type="button" aria-label="分镜节点">
            <Film size={17} />
            <span>分镜</span>
          </button>
          <button type="button" aria-label="导演节点" onClick={onOpenDirector}>
            <Video size={17} />
            <span>导演</span>
          </button>
        </aside>
        <WorkflowCanvas
          generationMode={settings.generationMode}
          model={settings.model}
          onOpenDirector={onOpenDirector}
          onToast={onToast}
        />
      </main>
    </div>
  )
}
