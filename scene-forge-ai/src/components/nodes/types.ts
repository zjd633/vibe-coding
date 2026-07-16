import type { Node } from '@xyflow/react'
import type { WorkflowNodeData, WorkflowNodeType } from '../../domain/workflow'

export type AppFlowNode = Node<WorkflowNodeData, WorkflowNodeType>
