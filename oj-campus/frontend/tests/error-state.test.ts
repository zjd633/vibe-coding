import { fireEvent, render, screen } from '@testing-library/vue'
import { describe, expect, it, vi } from 'vitest'
import AsyncState from '../src/components/AsyncState.vue'

describe('关键错误态', () => {
  it('展示可读错误并提供重试操作', async () => {
    const retry = vi.fn()
    render(AsyncState, { props: { status: 'error', message: '题目加载失败', onRetry: retry } })
    expect(screen.getByRole('alert').textContent).toContain('题目加载失败')
    await fireEvent.click(screen.getByRole('button', { name: '重新加载' }))
    expect(retry).toHaveBeenCalledOnce()
  })

  it('空状态不会误报为错误', () => {
    render(AsyncState, { props: { status: 'empty', message: '暂无提交记录' } })
    expect(screen.getByText('暂无提交记录')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
