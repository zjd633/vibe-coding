import { describe, expect, it, vi } from 'vitest'
import { startSubmissionPolling } from '../src/utils/polling'

describe('提交轮询', () => {
  it('遇到终态后停止每秒轮询', async () => {
    vi.useFakeTimers()
    const fetcher = vi.fn().mockResolvedValueOnce({ status: 'JUDGING' }).mockResolvedValueOnce({ status: 'AC' })
    const onUpdate = vi.fn()
    startSubmissionPolling(fetcher, onUpdate)
    await vi.advanceTimersByTimeAsync(1000)
    await vi.advanceTimersByTimeAsync(1000)
    await vi.advanceTimersByTimeAsync(3000)
    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(onUpdate).toHaveBeenLastCalledWith({ status: 'AC' })
    vi.useRealTimers()
  })

  it('组件卸载时可主动停止轮询', async () => {
    vi.useFakeTimers()
    const fetcher = vi.fn().mockResolvedValue({ status: 'PENDING' })
    const stop = startSubmissionPolling(fetcher, vi.fn())
    await vi.advanceTimersByTimeAsync(1000)
    stop()
    await vi.advanceTimersByTimeAsync(3000)
    expect(fetcher).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })
})
