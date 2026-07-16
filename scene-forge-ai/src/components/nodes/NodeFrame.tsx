import type { ReactNode } from 'react'
import { Handle, Position } from '@xyflow/react'

interface NodeFrameProps {
  title: string
  icon: ReactNode
  selected?: boolean
  accent?: 'cyan' | 'blue' | 'violet' | 'green'
  children: ReactNode
  wide?: boolean
}

export default function NodeFrame({
  title,
  icon,
  selected,
  accent = 'blue',
  children,
  wide,
}: NodeFrameProps) {
  return (
    <section
      className={`workflow-node node-accent-${accent}${selected ? ' is-selected' : ''}${wide ? ' is-wide' : ''}`}
    >
      <Handle className="node-handle" type="target" position={Position.Left} />
      <header className="workflow-node-header drag-handle">
        <span className="workflow-node-icon" aria-hidden="true">
          {icon}
        </span>
        <strong>{title}</strong>
        <span className="workflow-node-live">LIVE</span>
      </header>
      <div className="workflow-node-body">{children}</div>
      <Handle className="node-handle" type="source" position={Position.Right} />
    </section>
  )
}
