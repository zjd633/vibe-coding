import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import DirectorModal from './DirectorModal'

describe('DirectorModal', () => {
  it('adds a prop and exposes transform controls', () => {
    render(<DirectorModal open onClose={vi.fn()} onToast={vi.fn()} />)

    expect(screen.getByRole('dialog', { name: '3D 导演台' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '添加沙发' }))
    expect(screen.getAllByText('沙发 1')).toHaveLength(2)
    expect(screen.getByLabelText('X 位置')).toBeInTheDocument()
  })

  it('closes on Escape', () => {
    const onClose = vi.fn()
    render(<DirectorModal open onClose={onClose} onToast={vi.fn()} />)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('renders nothing while closed', () => {
    render(<DirectorModal open={false} onClose={vi.fn()} onToast={vi.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
