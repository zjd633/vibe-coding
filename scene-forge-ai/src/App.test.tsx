import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./components/WorkflowCanvas', () => ({
  default: () => <div data-testid="workflow-canvas-mock" />,
}))

describe('App navigation', () => {
  it('opens the demo project and returns to project management', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: '项目管理' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '打开项目 庭院漫剧' }))

    expect(screen.getByText('庭院漫剧')).toBeInTheDocument()
    expect(screen.getByRole('main', { name: '节点编辑器' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '返回项目管理' }))
    expect(screen.getByRole('heading', { name: '项目管理' })).toBeInTheDocument()
  })
})
