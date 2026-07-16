import { Box, Maximize2, Plus, Video } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import { useWorkflowActions } from '../WorkflowContext'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

export default function DirectorNode({ data, selected }: NodeProps<AppFlowNode>) {
  const actions = useWorkflowActions()
  return (
    <NodeFrame title={data.title} icon={<Video size={16} />} selected={selected} accent="cyan" wide>
      <div className="director-mini nodrag" aria-label="3D 导演预览">
        <div className="director-mini-grid" />
        <span className="mini-actor mini-actor-red" />
        <span className="mini-actor mini-actor-green" />
        <span className="mini-prop">
          <Box size={18} />
        </span>
      </div>
      <div className="director-actors">
        <span className="actor-chip actor-red">R1 赵安</span>
        <span className="actor-chip actor-green">R2 林晚</span>
        <button className="actor-add nodrag" type="button" aria-label="添加演员">
          <Plus size={13} /> 添加角色
        </button>
      </div>
      <button
        className="node-primary-action director-open nodrag"
        type="button"
        aria-label="打开全屏 3D 导演"
        onClick={actions.openDirector}
      >
        <Maximize2 size={16} /> 全屏操控
      </button>
      <button className="node-upload-zone nodrag" type="button">
        上传 360° 全景背景
      </button>
    </NodeFrame>
  )
}
