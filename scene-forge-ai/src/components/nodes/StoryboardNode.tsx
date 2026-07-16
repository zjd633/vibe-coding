import { Grid2X2, LoaderCircle, Sparkles } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import { useWorkflowActions } from '../WorkflowContext'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

export default function StoryboardNode({ id, data, selected }: NodeProps<AppFlowNode>) {
  const actions = useWorkflowActions()
  const loading = actions.loadingNodeId === id
  return (
    <NodeFrame title={data.title} icon={<Grid2X2 size={16} />} selected={selected} accent="green">
      <div className="storyboard-dimensions nodrag">
        <label>
          <span>行</span>
          <select
            aria-label="分镜行数"
            value={Number(data.rows ?? 2)}
            onChange={(event) => actions.updateNodeData(id, { rows: Number(event.target.value) })}
          >
            {[1, 2, 3].map((value) => (
              <option value={value} key={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <span>×</span>
        <label>
          <span>列</span>
          <select
            aria-label="分镜列数"
            value={Number(data.columns ?? 2)}
            onChange={(event) => actions.updateNodeData(id, { columns: Number(event.target.value) })}
          >
            {[1, 2, 3].map((value) => (
              <option value={value} key={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="node-field nodrag">
        <span>每行一个镜头描述</span>
        <textarea
          aria-label="分镜提示词"
          value={String(data.prompt ?? '')}
          onChange={(event) => actions.updateNodeData(id, { prompt: event.target.value })}
          rows={5}
        />
      </label>
      <button
        className="node-primary-action nodrag"
        type="button"
        disabled={loading}
        onClick={() => void actions.generateStoryboard(id)}
      >
        {loading ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}
        {loading ? '生成中…' : '生成分镜'}
      </button>
    </NodeFrame>
  )
}
