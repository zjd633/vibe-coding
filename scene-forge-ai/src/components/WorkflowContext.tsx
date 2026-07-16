import { createContext, useContext } from 'react'
import type { WorkflowNodeData } from '../domain/workflow'

export interface WorkflowActions {
  loadingNodeId: string | null
  updateNodeData: (nodeId: string, patch: Partial<WorkflowNodeData>) => void
  generateScene: (nodeId: string) => Promise<void>
  generateStoryboard: (nodeId: string) => Promise<void>
  openDirector: () => void
  previewPanorama: () => void
}

export const WorkflowActionsContext = createContext<WorkflowActions | null>(null)

export function useWorkflowActions(): WorkflowActions {
  const actions = useContext(WorkflowActionsContext)
  if (!actions) throw new Error('Workflow node must be rendered inside WorkflowActionsContext')
  return actions
}
