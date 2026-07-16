import { LayoutGrid } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

export default function StoryboardOutputNode({ data, selected }: NodeProps<AppFlowNode>) {
  const images = data.images ?? []
  return (
    <NodeFrame title={data.title} icon={<LayoutGrid size={16} />} selected={selected} accent="green" wide>
      <div className="storyboard-output-grid nodrag">
        {images.map((image, index) => (
          <figure key={`${image.slice(-20)}-${index}`}>
            <img src={image} alt={`分镜 ${index + 1}`} />
            <figcaption>SHOT {String(index + 1).padStart(2, '0')}</figcaption>
          </figure>
        ))}
      </div>
      {!images.length && <div className="node-empty-preview">等待分镜生成</div>}
    </NodeFrame>
  )
}
