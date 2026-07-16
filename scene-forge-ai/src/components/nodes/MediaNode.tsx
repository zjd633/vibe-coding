import { Images } from 'lucide-react'
import type { NodeProps } from '@xyflow/react'
import NodeFrame from './NodeFrame'
import type { AppFlowNode } from './types'

export default function MediaNode({ data, selected }: NodeProps<AppFlowNode>) {
  const images = data.images ?? []
  return (
    <NodeFrame title={data.title} icon={<Images size={16} />} selected={selected} accent="violet">
      <div className="media-node-grid">
        {images.map((image, index) => (
          <img key={`${image.slice(-20)}-${index}`} src={image} alt={`角色参考 ${index + 1}`} />
        ))}
      </div>
      <p className="node-helper">人物正面 / 侧面 / 服装参考</p>
    </NodeFrame>
  )
}
