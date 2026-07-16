import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import SettingsDialog, { type AppSettings } from './SettingsDialog'

const defaults: AppSettings = {
  generationMode: 'demo',
  model: 'demo-cinematic-v1',
}

describe('SettingsDialog', () => {
  it('validates the model name before saving API mode', () => {
    const onSave = vi.fn()
    render(<SettingsDialog open settings={defaults} onSave={onSave} onClose={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('生成模式'), { target: { value: 'api' } })
    fireEvent.change(screen.getByLabelText('模型名称'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: '保存设置' }))

    expect(screen.getByRole('alert')).toHaveTextContent('模型名称不能为空')
    expect(onSave).not.toHaveBeenCalled()
  })

  it('saves non-secret generation settings', () => {
    const onSave = vi.fn()
    render(<SettingsDialog open settings={defaults} onSave={onSave} onClose={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('生成模式'), { target: { value: 'api' } })
    fireEvent.change(screen.getByLabelText('模型名称'), { target: { value: 'my-image-model' } })
    fireEvent.click(screen.getByRole('button', { name: '保存设置' }))

    expect(onSave).toHaveBeenCalledWith({ generationMode: 'api', model: 'my-image-model' })
  })

  it('renders nothing while closed', () => {
    render(<SettingsDialog open={false} settings={defaults} onSave={vi.fn()} onClose={vi.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
