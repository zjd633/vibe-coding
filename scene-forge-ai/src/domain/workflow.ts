export type WorkflowNodeType =
  | 'media'
  | 'imagePrompt'
  | 'panorama'
  | 'director'
  | 'storyboard'
  | 'storyboardOutput'

export interface WorkflowNodeData {
  title: string
  prompt?: string
  image?: string
  images?: string[]
  rows?: number
  columns?: number
  [key: string]: unknown
}

export interface WorkflowNode {
  id: string
  type: WorkflowNodeType
  position: { x: number; y: number }
  data: WorkflowNodeData
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
}

export interface WorkflowState {
  version: 1
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

const nodes: WorkflowNode[] = [
  {
    id: 'media-characters',
    type: 'media',
    position: { x: 80, y: 470 },
    data: { title: '角色设定', images: [] },
  },
  {
    id: 'prompt-scene',
    type: 'imagePrompt',
    position: { x: 390, y: 520 },
    data: {
      title: 'AI 图片',
      prompt: '中国古代庭院，电影感，青瓦木廊，雨后薄雾，超宽全景',
    },
  },
  {
    id: 'panorama-main',
    type: 'panorama',
    position: { x: 760, y: 70 },
    data: { title: 'VR360 全景场景' },
  },
  {
    id: 'director-main',
    type: 'director',
    position: { x: 1190, y: 90 },
    data: { title: '3D 导演台', actorCount: 2 },
  },
  {
    id: 'storyboard-main',
    type: 'storyboard',
    position: { x: 1110, y: 610 },
    data: {
      title: '分镜生成',
      prompt: '男女主在长廊对话\n女主回头看向雨幕\n两人向庭院深处奔跑\n远景展示完整园林',
      rows: 2,
      columns: 2,
    },
  },
  {
    id: 'storyboard-output',
    type: 'storyboardOutput',
    position: { x: 1540, y: 590 },
    data: { title: '分镜输出', images: [] },
  },
]

const edges: WorkflowEdge[] = [
  { id: 'e-media-prompt', source: 'media-characters', target: 'prompt-scene' },
  { id: 'e-prompt-panorama', source: 'prompt-scene', target: 'panorama-main' },
  { id: 'e-panorama-director', source: 'panorama-main', target: 'director-main' },
  { id: 'e-media-storyboard', source: 'media-characters', target: 'storyboard-main' },
  { id: 'e-director-storyboard', source: 'director-main', target: 'storyboard-main' },
  { id: 'e-storyboard-output', source: 'storyboard-main', target: 'storyboard-output' },
]

export function createDefaultWorkflow(): WorkflowState {
  return {
    version: 1,
    nodes: structuredClone(nodes),
    edges: structuredClone(edges),
  }
}

export function parseStoryboardPrompts(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
}

export function serializeWorkflow(workflow: WorkflowState): string {
  return JSON.stringify(workflow)
}

function isWorkflowState(value: unknown): value is WorkflowState {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<WorkflowState>
  return candidate.version === 1 && Array.isArray(candidate.nodes) && Array.isArray(candidate.edges)
}

export function deserializeWorkflow(value: string | null): WorkflowState {
  if (!value) return createDefaultWorkflow()
  try {
    const parsed: unknown = JSON.parse(value)
    return isWorkflowState(parsed) ? parsed : createDefaultWorkflow()
  } catch {
    return createDefaultWorkflow()
  }
}
