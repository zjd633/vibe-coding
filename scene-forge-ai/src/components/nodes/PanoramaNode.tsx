import { Expand, Globe2, ImageDown } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import { useRef } from 'react'
import { useWorkflowActions } from '../WorkflowContext'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

export default function PanoramaNode({ id, data, selected }: NodeProps<AppFlowNode>) {
  const actions = useWorkflowActions()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const importImage = (file: File | undefined) => {
    if (!file || !file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.addEventListener('load', () => {
      if (typeof reader.result === 'string') actions.updateNodeData(id, { image: reader.result })
    })
    reader.readAsDataURL(file)
  }

  const exportImage = () => {
    if (!data.image) return
    const link = document.createElement('a')
    link.href = String(data.image)
    link.download = 'sceneforge-panorama.png'
    link.click()
  }
  return (
    <NodeFrame title={data.title} icon={<Globe2 size={16} />} selected={selected} accent="cyan" wide>
      <div className="panorama-preview nodrag">
        {data.image ? (
          <img src={String(data.image)} alt="VR360 全景场景预览" />
        ) : (
          <div className="node-empty-preview">等待场景图片</div>
        )}
        <span>拖动查看 360° 场景</span>
      </div>
      <div className="node-action-grid nodrag">
        <button type="button" onClick={actions.previewPanorama}>
          <Expand size={15} /> 360° 沉浸预览
        </button>
        <button type="button" onClick={exportImage} disabled={!data.image}>
          <ImageDown size={15} /> 单张导出
        </button>
      </div>
      <input
        ref={fileInputRef}
        className="visually-hidden-input nodrag"
        type="file"
        accept="image/*"
        aria-label="选择全景图片"
        onChange={(event) => importImage(event.target.files?.[0])}
      />
      <button
        className="node-upload-zone nodrag"
        type="button"
        onClick={() => fileInputRef.current?.click()}
      >
        上传全景图
      </button>
    </NodeFrame>
  )
}
