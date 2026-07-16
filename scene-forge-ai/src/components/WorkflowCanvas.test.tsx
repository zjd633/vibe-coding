import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import WorkflowCanvas from './WorkflowCanvas'

describe('WorkflowCanvas', () => {
  beforeEach(() => localStorage.clear())

  it('registers and renders the six reference node types', () => {
    render(
      <WorkflowCanvas
        generationMode="demo"
        model="demo-cinematic-v1"
        onOpenDirector={vi.fn()}
        onToast={vi.fn()}
      />,
    )

    expect(screen.getByText('角色设定')).toBeInTheDocument()
    expect(screen.getByText('AI 图片')).toBeInTheDocument()
    expect(screen.getByText('VR360 全景场景')).toBeInTheDocument()
    expect(screen.getByText('3D 导演台')).toBeInTheDocument()
    expect(screen.getByText('分镜生成')).toBeInTheDocument()
    expect(screen.getByText('分镜输出')).toBeInTheDocument()
  })

  it('updates a prompt and generates a panorama in demo mode', async () => {
    render(
      <WorkflowCanvas
        generationMode="demo"
        model="demo-cinematic-v1"
        onOpenDirector={vi.fn()}
        onToast={vi.fn()}
      />,
    )

    fireEvent.change(screen.getByLabelText('场景提示词'), {
      target: { value: '雨夜长廊，电影感' },
    })
    fireEvent.click(screen.getByLabelText('生成场景图片'))

    await waitFor(() => {
      expect(screen.getByAltText('VR360 全景场景预览')).toHaveAttribute(
        'src',
        expect.stringContaining('data:image/svg+xml'),
      )
    })
    expect(localStorage.getItem('sceneforge.workflow')).toContain('雨夜长廊')
  })

  it('opens the fullscreen director from the director node', () => {
    const onOpenDirector = vi.fn()
    render(
      <WorkflowCanvas
        generationMode="demo"
        model="demo-cinematic-v1"
        onOpenDirector={onOpenDirector}
        onToast={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByLabelText('打开全屏 3D 导演'))
    expect(onOpenDirector).toHaveBeenCalledOnce()
  })

  it('imports a local panorama image into the panorama node', async () => {
    render(
      <WorkflowCanvas
        generationMode="demo"
        model="demo-cinematic-v1"
        onOpenDirector={vi.fn()}
        onToast={vi.fn()}
      />,
    )
    const file = new File(['panorama'], 'garden.png', { type: 'image/png' })

    fireEvent.change(screen.getByLabelText('选择全景图片'), { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByAltText('VR360 全景场景预览').getAttribute('src')).toMatch(
        /^data:image\/png;base64,/,
      )
    })
  })
})
