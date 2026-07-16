import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  createDefaultWorkflow,
  deserializeWorkflow,
  parseStoryboardPrompts,
  serializeWorkflow,
  type WorkflowNodeData,
  type WorkflowState,
} from '../domain/workflow'
import { createDemoImage } from '../lib/demoImage'
import { generateImages } from '../lib/generateImage'
import { WorkflowActionsContext } from './WorkflowContext'
import DirectorNode from './nodes/DirectorNode'
import ImagePromptNode from './nodes/ImagePromptNode'
import MediaNode from './nodes/MediaNode'
import PanoramaNode from './nodes/PanoramaNode'
import StoryboardNode from './nodes/StoryboardNode'
import StoryboardOutputNode from './nodes/StoryboardOutputNode'
import type { AppFlowNode } from './nodes/types'

const storageKey = 'sceneforge.workflow'

const nodeTypes: NodeTypes = {
  media: MediaNode,
  imagePrompt: ImagePromptNode,
  panorama: PanoramaNode,
  director: DirectorNode,
  storyboard: StoryboardNode,
  storyboardOutput: StoryboardOutputNode,
}

interface WorkflowCanvasProps {
  generationMode: 'demo' | 'api'
  model: string
  onOpenDirector: () => void
  onToast: (message: string, tone?: 'success' | 'error' | 'info') => void
}

function hydrateDemoAssets(workflow: WorkflowState): WorkflowState {
  return {
    ...workflow,
    nodes: workflow.nodes.map((node) => {
      if (node.type === 'media' && !(node.data.images?.length ?? 0)) {
        return {
          ...node,
          data: {
            ...node.data,
            images: [
              createDemoImage('男主角色设定，青衣侠客', 0, 260, 320),
              createDemoImage('女主角色设定，白衣少女', 1, 260, 320),
              createDemoImage('反派角色设定，深色长袍', 2, 260, 320),
            ],
          },
        }
      }
      if (node.type === 'panorama' && !node.data.image) {
        return {
          ...node,
          data: {
            ...node.data,
            image: createDemoImage('中国古代庭院，全景长廊，雨后薄雾', 0, 900, 440),
          },
        }
      }
      if (node.type === 'storyboardOutput' && !(node.data.images?.length ?? 0)) {
        return {
          ...node,
          data: {
            ...node.data,
            images: Array.from({ length: 4 }, (_, index) =>
              createDemoImage('古风庭院连续分镜', index, 420, 260),
            ),
          },
        }
      }
      return node
    }),
  }
}

function initialWorkflow(): WorkflowState {
  const stored = deserializeWorkflow(localStorage.getItem(storageKey))
  return hydrateDemoAssets(stored)
}

export default function WorkflowCanvas({
  generationMode,
  model,
  onOpenDirector,
  onToast,
}: WorkflowCanvasProps) {
  const initial = useMemo(initialWorkflow, [])
  const [nodes, setNodes, onNodesChange] = useNodesState<AppFlowNode>(initial.nodes as AppFlowNode[])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(
    initial.edges.map((edge) => ({ ...edge, animated: true, className: 'workflow-edge' })),
  )
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null)

  const updateNodeData = useCallback(
    (nodeId: string, patch: Partial<WorkflowNodeData>) => {
      setNodes((current) =>
        current.map((node) =>
          node.id === nodeId ? { ...node, data: { ...node.data, ...patch } } : node,
        ),
      )
    },
    [setNodes],
  )

  const generateScene = useCallback(
    async (nodeId: string) => {
      const node = nodes.find((candidate) => candidate.id === nodeId)
      const prompt = String(node?.data.prompt ?? '').trim()
      if (!prompt) return
      setLoadingNodeId(nodeId)
      try {
        const [image] = await generateImages({
          mode: generationMode,
          prompt,
          count: 1,
          width: 1024,
          height: 576,
          model,
        })
        updateNodeData(nodeId, { image })
        updateNodeData('panorama-main', { image })
        onToast('场景图片已生成并连接到 VR360 节点。', 'success')
      } catch (error) {
        onToast(error instanceof Error ? error.message : '场景生成失败。', 'error')
      } finally {
        setLoadingNodeId(null)
      }
    },
    [generationMode, model, nodes, onToast, updateNodeData],
  )

  const generateStoryboard = useCallback(
    async (nodeId: string) => {
      const node = nodes.find((candidate) => candidate.id === nodeId)
      const lines = parseStoryboardPrompts(String(node?.data.prompt ?? ''))
      const count = Math.min(Number(node?.data.rows ?? 2) * Number(node?.data.columns ?? 2), 9)
      const prompt = lines.slice(0, count).join('；') || '古风连续分镜'
      setLoadingNodeId(nodeId)
      try {
        const images = await generateImages({
          mode: generationMode,
          prompt,
          count,
          width: 640,
          height: 400,
          model,
        })
        updateNodeData('storyboard-output', { images })
        onToast(`已生成 ${images.length} 个连续分镜。`, 'success')
      } catch (error) {
        onToast(error instanceof Error ? error.message : '分镜生成失败。', 'error')
      } finally {
        setLoadingNodeId(null)
      }
    },
    [generationMode, model, nodes, onToast, updateNodeData],
  )

  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((current) =>
        addEdge({ ...connection, animated: true, className: 'workflow-edge' }, current),
      ),
    [setEdges],
  )

  useEffect(() => {
    const workflow: WorkflowState = {
      version: 1,
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type!,
        position: node.position,
        data: node.data,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle ?? undefined,
        targetHandle: edge.targetHandle ?? undefined,
      })),
    }
    localStorage.setItem(storageKey, serializeWorkflow(workflow))
  }, [edges, nodes])

  const actions = useMemo(
    () => ({
      loadingNodeId,
      updateNodeData,
      generateScene,
      generateStoryboard,
      openDirector: onOpenDirector,
      previewPanorama: () => onToast('沉浸预览将在当前全景场景中打开。', 'info'),
    }),
    [generateScene, generateStoryboard, loadingNodeId, onOpenDirector, onToast, updateNodeData],
  )

  return (
    <WorkflowActionsContext value={actions}>
      <div className="workflow-canvas" data-testid="workflow-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          fitViewOptions={{ padding: 0.16, maxZoom: 0.88 }}
          minZoom={0.25}
          maxZoom={1.5}
          panOnScroll
          selectionOnDrag
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1.1} color="#344050" />
          <MiniMap
            className="workflow-minimap"
            nodeColor={(node) => (node.type === 'director' || node.type === 'panorama' ? '#27c7e5' : '#49566a')}
            maskColor="rgb(5 7 10 / 78%)"
            pannable
            zoomable
          />
          <Controls className="workflow-controls" showInteractive={false} />
        </ReactFlow>
      </div>
    </WorkflowActionsContext>
  )
}
