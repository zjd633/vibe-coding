import { LoaderCircle, Sparkles, WandSparkles } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import { useWorkflowActions } from '../WorkflowContext'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

const tags = ['人设', '三视图', '360°', '写实', '2D', '3D', '国漫', '广角']

export default function ImagePromptNode({ id, data, selected }: NodeProps<AppFlowNode>) {
  const actions = useWorkflowActions()
  const loading = actions.loadingNodeId === id
  const prompt = String(data.prompt ?? '')

  const appendTag = (tag: string) => {
    if (prompt.includes(tag)) return
    actions.updateNodeData(id, { prompt: `${prompt}${prompt ? '，' : ''}${tag}` })
  }

  return (
    <NodeFrame title={data.title} icon={<WandSparkles size={16} />} selected={selected} accent="blue">
      <div className="node-tag-row nodrag">
        {tags.map((tag) => (
          <button type="button" key={tag} onClick={() => appendTag(tag)}>
            {tag}
          </button>
        ))}
      </div>
      <label className="node-field nodrag">
        <span>场景提示词</span>
        <textarea
          aria-label="场景提示词"
          value={prompt}
          onChange={(event) => actions.updateNodeData(id, { prompt: event.target.value })}
          rows={5}
        />
      </label>
      <div className="node-inline-options nodrag">
        <span>
          <Sparkles size={13} aria-hidden="true" /> Nano Banana 2
        </span>
        <span>16:9 · 2K</span>
      </div>
      <button
        className="node-primary-action nodrag"
        type="button"
        aria-label="生成场景图片"
        disabled={loading || !prompt.trim()}
        onClick={() => void actions.generateScene(id)}
      >
        {loading ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}
        {loading ? '生成中…' : '生成'}
      </button>
    </NodeFrame>
  )
}
