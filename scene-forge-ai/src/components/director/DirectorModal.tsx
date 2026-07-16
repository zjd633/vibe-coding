import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Armchair,
  Box,
  Camera,
  CircleUserRound,
  Download,
  LampFloor,
  PanelTop,
  Plus,
  RotateCcw,
  Square,
  Table2,
  Trash2,
  X,
} from 'lucide-react'
import {
  addDirectorItem,
  cameraPresets,
  createDirectorState,
  removeDirectorItem,
  selectDirectorItem,
  updateDirectorItem,
  type CameraPresetId,
  type DirectorItemKind,
} from '../../domain/director'
import ThreeViewport, { type DirectorExporter } from './ThreeViewport'

interface DirectorModalProps {
  open: boolean
  onClose: () => void
  onToast: (message: string, tone?: 'success' | 'error' | 'info') => void
}

const propButtons: Array<{
  kind: DirectorItemKind
  label: string
  icon: typeof Box
}> = [
  { kind: 'sofa', label: '沙发', icon: Armchair },
  { kind: 'table', label: '桌子', icon: Table2 },
  { kind: 'chair', label: '椅子', icon: Armchair },
  { kind: 'wall', label: '墙体', icon: PanelTop },
  { kind: 'lamp', label: '灯光', icon: LampFloor },
  { kind: 'cube', label: '几何体', icon: Square },
]

export default function DirectorModal({ open, onClose, onToast }: DirectorModalProps) {
  const [state, setState] = useState(createDirectorState)
  const [cameraPreset, setCameraPreset] = useState<CameraPresetId>('wide')
  const [exporter, setExporter] = useState<DirectorExporter | null>(null)
  const [libraryTab, setLibraryTab] = useState<'props' | 'actors'>('props')
  const selected = useMemo(
    () => state.items.find((item) => item.id === state.selectedId) ?? null,
    [state],
  )

  useEffect(() => {
    if (!open) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [onClose, open])

  const selectItem = useCallback((itemId: string) => {
    setState((current) => selectDirectorItem(current, itemId))
  }, [])

  const updatePosition = (axis: 0 | 1 | 2, value: number) => {
    if (!selected) return
    const position = [...selected.position] as [number, number, number]
    position[axis] = value
    setState((current) => updateDirectorItem(current, selected.id, { position }))
  }

  const updateRotation = (value: number) => {
    if (!selected) return
    setState((current) =>
      updateDirectorItem(current, selected.id, { rotation: [0, value, 0] }),
    )
  }

  const exportView = (mode: 'color' | 'depth') => {
    if (!exporter) {
      onToast('3D 渲染器仍在准备，请稍后重试。', 'info')
      return
    }
    if (mode === 'color') exporter.exportColor()
    else exporter.exportDepth()
    onToast(mode === 'color' ? '已导出当前彩色视角。' : '已导出当前深度图。', 'success')
  }

  if (!open) return null

  return (
    <div className="director-scrim">
      <section
        className="director-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="director-modal-title"
      >
        <header className="director-topbar">
          <div>
            <p>SCENEFORGE / SPATIAL BLOCKING</p>
            <h2 id="director-modal-title">3D 导演台</h2>
          </div>
          <nav className="camera-presets" aria-label="镜头预设">
            {(Object.keys(cameraPresets) as CameraPresetId[]).map((id) => (
              <button
                type="button"
                className={cameraPreset === id ? 'is-active' : ''}
                aria-pressed={cameraPreset === id}
                key={id}
                onClick={() => setCameraPreset(id)}
              >
                <Camera size={14} aria-hidden="true" />
                {cameraPresets[id].label}
              </button>
            ))}
          </nav>
          <button className="icon-button director-close" type="button" aria-label="退出全屏" onClick={onClose}>
            <X size={20} aria-hidden="true" />
          </button>
        </header>

        <div className="director-workspace">
          <aside className="director-library" aria-label="场景素材库">
            <div className="director-tabs" role="tablist" aria-label="素材类型">
              <button
                type="button"
                role="tab"
                aria-selected={libraryTab === 'props'}
                className={libraryTab === 'props' ? 'is-active' : ''}
                onClick={() => setLibraryTab('props')}
              >
                常用道具
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={libraryTab === 'actors'}
                className={libraryTab === 'actors' ? 'is-active' : ''}
                onClick={() => setLibraryTab('actors')}
              >
                人物角色
              </button>
            </div>

            {libraryTab === 'props' ? (
              <div className="director-tool-grid">
                {propButtons.map(({ kind, label, icon: Icon }) => (
                  <button
                    type="button"
                    aria-label={`添加${label}`}
                    key={kind}
                    onClick={() => setState((current) => addDirectorItem(current, 'prop', kind))}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="director-tool-grid actor-tools">
                <button
                  type="button"
                  aria-label="添加红色角色"
                  onClick={() => setState((current) => addDirectorItem(current, 'actor', 'actor', '#ef5545'))}
                >
                  <CircleUserRound size={21} />
                  <span>红色角色</span>
                </button>
                <button
                  type="button"
                  aria-label="添加绿色角色"
                  onClick={() => setState((current) => addDirectorItem(current, 'actor', 'actor', '#31cf91'))}
                >
                  <CircleUserRound size={21} />
                  <span>绿色角色</span>
                </button>
                <button
                  type="button"
                  aria-label="添加蓝色角色"
                  onClick={() => setState((current) => addDirectorItem(current, 'actor', 'actor', '#4d9aff'))}
                >
                  <CircleUserRound size={21} />
                  <span>蓝色角色</span>
                </button>
              </div>
            )}

            <div className="scene-list-heading">
              <span>场景对象</span>
              <span>{state.items.length}</span>
            </div>
            <div className="scene-object-list">
              {state.items.map((item) => (
                <button
                  type="button"
                  className={item.id === state.selectedId ? 'is-selected' : ''}
                  key={item.id}
                  onClick={() => selectItem(item.id)}
                >
                  <span className="scene-object-swatch" style={{ backgroundColor: item.color }} />
                  <span>{item.name}</span>
                </button>
              ))}
            </div>
          </aside>

          <div className="director-stage">
            <ThreeViewport
              items={state.items}
              selectedId={state.selectedId}
              cameraPreset={cameraPreset}
              onSelect={selectItem}
              onExporter={setExporter}
            />
            <div className="director-stage-badge">
              <span className="live-dot" /> 实时场景
            </div>
            <div className="director-export-bar">
              <button type="button" onClick={() => exportView('color')}>
                <Download size={16} /> 导出当前视角
              </button>
              <button type="button" onClick={() => exportView('depth')}>
                <Download size={16} /> 导出深度图
              </button>
              <button className="danger-action" type="button" onClick={onClose}>
                退出全屏
              </button>
            </div>
          </div>

          <aside className="director-inspector" aria-label="对象属性">
            <div className="inspector-heading">
              <div>
                <p>SELECTED OBJECT</p>
                <h3>{selected?.name ?? '未选择对象'}</h3>
              </div>
              {selected && (
                <button
                  className="icon-button"
                  type="button"
                  aria-label="删除选中对象"
                  onClick={() => setState((current) => removeDirectorItem(current, selected.id))}
                >
                  <Trash2 size={17} />
                </button>
              )}
            </div>

            {selected ? (
              <div className="inspector-controls">
                <fieldset>
                  <legend>位置</legend>
                  {(['X', 'Y', 'Z'] as const).map((axis, index) => (
                    <label key={axis}>
                      <span>{axis}</span>
                      <input
                        aria-label={`${axis} 位置`}
                        type="range"
                        min={index === 1 ? 0 : -6}
                        max={6}
                        step={0.1}
                        value={selected.position[index]}
                        onChange={(event) => updatePosition(index as 0 | 1 | 2, Number(event.target.value))}
                      />
                      <output>{selected.position[index].toFixed(1)}</output>
                    </label>
                  ))}
                </fieldset>
                <fieldset>
                  <legend>旋转与大小</legend>
                  <label>
                    <RotateCcw size={14} />
                    <input
                      aria-label="Y 轴旋转"
                      type="range"
                      min={-3.14}
                      max={3.14}
                      step={0.05}
                      value={selected.rotation[1]}
                      onChange={(event) => updateRotation(Number(event.target.value))}
                    />
                    <output>{Math.round((selected.rotation[1] * 180) / Math.PI)}°</output>
                  </label>
                  <label>
                    <Plus size={14} />
                    <input
                      aria-label="对象大小"
                      type="range"
                      min={0.35}
                      max={2.5}
                      step={0.05}
                      value={selected.scale}
                      onChange={(event) =>
                        setState((current) =>
                          updateDirectorItem(current, selected.id, { scale: Number(event.target.value) }),
                        )
                      }
                    />
                    <output>{selected.scale.toFixed(2)}</output>
                  </label>
                </fieldset>
              </div>
            ) : (
              <div className="inspector-empty">从场景中选择一个人物或道具。</div>
            )}
          </aside>
        </div>
      </section>
    </div>
  )
}
