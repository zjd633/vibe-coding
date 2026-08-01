import { fireEvent, render, screen, waitFor } from '@testing-library/vue'
import axios from 'axios'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, readableError } from '../src/api/client'
import { useAuthStore } from '../src/stores/auth'
import { startSubmissionPolling } from '../src/utils/polling'
import SubmissionDetailView from '../src/views/SubmissionDetailView.vue'
import PublicSubmissionsView from '../src/views/PublicSubmissionsView.vue'
import SettingsView from '../src/views/SettingsView.vue'
import AdminProblemEditorView from '../src/views/admin/AdminProblemEditorView.vue'
import AdminProblemsView from '../src/views/admin/AdminProblemsView.vue'
import AdminSubmissionsView from '../src/views/admin/AdminSubmissionsView.vue'

const submission = (overrides = {}) => ({
  id: 12, user_id: 4, problem_id: 8, problem_revision: 1, language: 'cpp17' as const,
  status: 'PENDING' as const, runtime_ms: null, created_at: '2026-07-26T00:00:00Z', ...overrides,
})

async function renderAt(component: object, path: string, routes = [{ path, component }]) {
  const router = createRouter({ history: createMemoryHistory(), routes: [...routes, { path: '/:pathMatch(.*)*', component: { template: '<div />' } }] })
  await router.push(path)
  await router.isReady()
  return { router, ...render(component, { global: { plugins: [router] } }) }
}

afterEach(() => vi.restoreAllMocks())

describe('Task 3 页面韧性', () => {
  it('轮询请求失败时通知错误并彻底停止后续调度', async () => {
    vi.useFakeTimers()
    const fetcher = vi.fn().mockRejectedValue(new Error('offline'))
    const onError = vi.fn()
    startSubmissionPolling(fetcher, vi.fn(), onError)
    await vi.advanceTimersByTimeAsync(1000)
    expect(onError).toHaveBeenCalledOnce()
    await vi.advanceTimersByTimeAsync(3000)
    expect(fetcher).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })

  it('提交详情在轮询失败后显示可重试错误，重试才重启轮询且卸载会清理', async () => {
    vi.useFakeTimers()
    const get = vi.spyOn(api, 'get')
      .mockResolvedValueOnce({ data: submission() })
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ data: submission() })
      .mockResolvedValueOnce({ data: submission({ status: 'AC', runtime_ms: 8 }) })
    const { unmount } = await renderAt(SubmissionDetailView, '/submissions/12')
    await screen.findByText('评测进行中，本页每秒自动更新。')
    await vi.advanceTimersByTimeAsync(1000)
    expect(screen.getByRole('alert').textContent).toContain('评测状态更新失败')
    const failedCalls = get.mock.calls.length
    await vi.advanceTimersByTimeAsync(3000)
    expect(get).toHaveBeenCalledTimes(failedCalls)
    await fireEvent.click(screen.getByRole('button', { name: '重新获取评测状态' }))
    await screen.findByText('评测进行中，本页每秒自动更新。')
    await vi.advanceTimersByTimeAsync(1000)
    expect(screen.getByRole('heading', { name: '答案正确' })).toBeTruthy()
    unmount()
    await vi.advanceTimersByTimeAsync(3000)
    expect(get).toHaveBeenCalledTimes(4)
    vi.useRealTimers()
  })

  it('卸载尚在评测的详情页后不会继续请求', async () => {
    vi.useFakeTimers()
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: submission() })
    const { unmount } = await renderAt(SubmissionDetailView, '/submissions/12')
    await screen.findByText('评测进行中，本页每秒自动更新。')
    unmount()
    await vi.advanceTimersByTimeAsync(4000)
    expect(get).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })

  it('已停止的在途轮询失败不会再触发错误回调', async () => {
    vi.useFakeTimers()
    let rejectFetch: (cause: Error) => void = () => undefined
    const fetcher = vi.fn(() => new Promise<{ status: string }>((_resolve, reject) => { rejectFetch = reject }))
    const onError = vi.fn()
    const stop = startSubmissionPolling(fetcher, vi.fn(), onError)
    vi.advanceTimersByTime(1000)
    await Promise.resolve()
    stop()
    rejectFetch(new Error('offline'))
    await Promise.resolve()
    expect(onError).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('密码更新成功后即使注销 Cookie 失败也清空本地认证并前往登录页', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.updateUser({ id: 1, username: 'lin', display_name: '林同学', email: 'lin@example.com', role: 'student', is_active: true, created_at: '2026-01-01' })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/settings', component: SettingsView }, { path: '/login', component: { template: '<h1>登录</h1>' } }] })
    await router.push('/settings')
    await router.isReady()
    vi.spyOn(api, 'patch').mockResolvedValue({ data: undefined })
    vi.spyOn(api, 'post').mockRejectedValue(new Error('session already invalidated'))
    render(SettingsView, { global: { plugins: [pinia, router] } })
    await fireEvent.update(screen.getByLabelText('当前密码'), 'old-password')
    await fireEvent.update(screen.getByLabelText('新密码'), 'new-password')
    await fireEvent.click(screen.getByRole('button', { name: '更新密码' }))
    await waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))
    expect(auth.user).toBeNull()
  })

  it('创建题目时加载已有标签、创建标签并且仅提交已选择的有效标签', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 1, name: 'math' }] })
    const post = vi.spyOn(api, 'post').mockResolvedValueOnce({ data: { id: 2, name: 'graphs' } }).mockResolvedValueOnce({ data: { id: 9 } })
    const { router } = await renderAt(AdminProblemEditorView, '/admin/problems/new')
    await screen.findByRole('checkbox', { name: 'math' })
    await fireEvent.update(screen.getByLabelText('新标签'), 'graphs')
    await fireEvent.click(screen.getByRole('button', { name: '创建标签' }))
    await screen.findByRole('checkbox', { name: 'graphs' })
    await fireEvent.update(screen.getByLabelText('题目名称'), '图论入门')
    await fireEvent.update(screen.getByLabelText('题目描述'), '给定一张图。')
    await fireEvent.click(screen.getByRole('button', { name: '保存题目' }))
    await waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/problems'))
    expect(get).toHaveBeenCalledWith('/admin/tags')
    expect(post).toHaveBeenLastCalledWith('/admin/problems', expect.objectContaining({ tags: ['graphs'] }))
  })

  it('编辑题目同样加载可选择标签', async () => {
    const get = vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url === '/admin/tags') return Promise.resolve({ data: [{ id: 1, name: 'math' }] })
      return Promise.resolve({ data: { id: 7, title: 'A+B', statement: '题面', input: '', output: '', difficulty: 'easy', time_limit_ms: 1000, published: false, revision: 1, tags: ['math'], test_cases: [] } })
    })
    await renderAt(AdminProblemEditorView, '/admin/problems/7/edit', [{ path: '/admin/problems/:id/edit', component: AdminProblemEditorView }])
    const math = await screen.findByRole('checkbox', { name: 'math' }) as HTMLInputElement
    await waitFor(() => expect(math.checked).toBe(true))
    expect(get).toHaveBeenCalledWith('/admin/tags')
  })

  it('编辑已有题目时不会把只读测试点 position 回传给严格 PUT 接口', async () => {
    vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url === '/admin/tags') return Promise.resolve({ data: [{ id: 1, name: 'math' }] })
      return Promise.resolve({
        data: {
          id: 7, title: 'A+B', statement: '题面', input: '两个整数', output: '和', difficulty: 'easy',
          time_limit_ms: 1000, published: true, revision: 1, tags: ['math'],
          test_cases: [{ input: '1 2\n', output: '3\n', is_sample: true, position: 1 }],
        },
      })
    })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: {} })
    const { router } = await renderAt(AdminProblemEditorView, '/admin/problems/7/edit', [{ path: '/admin/problems/:id/edit', component: AdminProblemEditorView }])
    await screen.findByDisplayValue('A+B')
    await fireEvent.update(screen.getByLabelText('题目名称'), 'A+B 修订版')
    await fireEvent.click(screen.getByRole('button', { name: '保存题目' }))
    await waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/problems'))
    expect(put).toHaveBeenCalledWith('/admin/problems/7', expect.objectContaining({
      title: 'A+B 修订版',
      test_cases: [{ input: '1 2\n', output: '3\n', is_sample: true }],
    }))
    expect((put.mock.calls[0]?.[1] as { test_cases: object[] }).test_cases[0]).not.toHaveProperty('position')
  })

  it('编辑题目会在标签尚未加载完成时阻止保存，避免覆盖既有标签', async () => {
    let resolveTags: (value: { data: { id: number; name: string }[] }) => void = () => undefined
    const get = vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url === '/admin/tags') return new Promise(resolve => { resolveTags = resolve })
      return Promise.resolve({ data: { id: 7, title: 'A+B', statement: '题面', input: '', output: '', difficulty: 'easy', time_limit_ms: 1000, published: false, revision: 1, tags: ['math'], test_cases: [] } })
    })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: {} })
    await renderAt(AdminProblemEditorView, '/admin/problems/7/edit', [{ path: '/admin/problems/:id/edit', component: AdminProblemEditorView }])
    await screen.findByDisplayValue('A+B')
    await fireEvent.click(screen.getByRole('button', { name: '保存题目' }))
    expect(screen.getByRole('alert').textContent).toContain('标签尚未加载完成')
    expect(put).not.toHaveBeenCalled()
    resolveTags({ data: [{ id: 1, name: 'math' }] })
    await waitFor(() => expect(get).toHaveBeenCalledWith('/admin/tags'))
  })

  it('标签加载失败后可局部重试，并保留编辑中的表单内容再保存', async () => {
    let tagRequests = 0
    const get = vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url === '/admin/tags') {
        tagRequests += 1
        return tagRequests === 1
          ? Promise.reject(new Error('offline'))
          : Promise.resolve({ data: [{ id: 1, name: 'math' }] })
      }
      return Promise.resolve({ data: { id: 7, title: 'A+B', statement: '原题面', input: '原输入', output: '原输出', difficulty: 'easy', time_limit_ms: 1000, published: false, revision: 1, tags: ['math'], test_cases: [{ input: '1 2', output: '3', is_sample: true }] } })
    })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: {} })
    await renderAt(AdminProblemEditorView, '/admin/problems/7/edit', [{ path: '/admin/problems/:id/edit', component: AdminProblemEditorView }])
    await screen.findByText('标签加载失败')
    await fireEvent.update(screen.getByLabelText('题目名称'), '保留的新标题')
    await fireEvent.update(screen.getByLabelText('题目描述'), '保留的新题面')
    await fireEvent.update(screen.getByLabelText('输入'), '9 9')
    await fireEvent.click(screen.getByRole('button', { name: '保存题目' }))
    expect(screen.getAllByRole('alert').some(alert => alert.textContent?.includes('标签加载失败，请重新加载后再保存'))).toBe(true)
    await fireEvent.click(screen.getByRole('button', { name: '重新加载标签' }))
    const math = await screen.findByRole('checkbox', { name: 'math' }) as HTMLInputElement
    await waitFor(() => expect(math.checked).toBe(true))
    expect(screen.getByDisplayValue('保留的新标题')).toBeTruthy()
    expect(screen.getByDisplayValue('保留的新题面')).toBeTruthy()
    expect(screen.getByDisplayValue('9 9')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
    await fireEvent.click(screen.getByRole('button', { name: '保存题目' }))
    await waitFor(() => expect(put).toHaveBeenCalledWith('/admin/problems/7', expect.objectContaining({ title: '保留的新标题', statement: '保留的新题面', tags: ['math'], test_cases: [expect.objectContaining({ input: '9 9' })] })))
  })

  it('将标签相关后端错误翻译为明确中文提示', () => {
    const error = { isAxiosError: true, response: { data: { code: 'invalid_tag', message: 'unknown tag' } } }
    vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)
    expect(readableError(error)).toContain('标签')
  })

  it('管理员查看提交详情失败时保留列表、展示告警并允许重试', async () => {
    const get = vi.spyOn(api, 'get')
      .mockResolvedValueOnce({ data: [submission({ status: 'AC' })] })
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ data: submission({ status: 'AC', source: 'int main(){}' }) })
    await renderAt(AdminSubmissionsView, '/admin/submissions')
    await screen.findByText('#12')
    await fireEvent.click(screen.getByRole('button', { name: '查看详情' }))
    expect((await screen.findByRole('alert')).textContent).toContain('提交详情加载失败')
    expect(screen.getByText('#12')).toBeTruthy()
    await fireEvent.click(screen.getByRole('button', { name: '重新查看详情' }))
    expect(await screen.findByText('提交 #12')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(get).toHaveBeenCalledTimes(3)
  })

  it('管理员删除题目失败时保留列表并展示告警', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 7, title: 'A+B', statement: '题面', input: '', output: '', difficulty: 'easy', time_limit_ms: 1000, published: true, revision: 1, tags: [] }] })
    vi.spyOn(api, 'delete').mockRejectedValue(new Error('offline'))
    await renderAt(AdminProblemsView, '/admin/problems')
    await screen.findByText('A+B')
    await fireEvent.click(screen.getByRole('button', { name: '删除 A+B' }))
    expect((await screen.findByRole('alert')).textContent).toContain('题目删除失败')
    expect(screen.getByText('A+B')).toBeTruthy()
  })

  it('全站提交页面不会将意外返回的源码、诊断或失败用例传给展示表格', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [submission({ status: 'WA', source: '<script>leak-source</script>', details: 'leak-details', failed_case: 99 })], page: 1, page_size: 20, total: 1 } })
    await renderAt(PublicSubmissionsView, '/submissions/public')
    await screen.findByText('#12')
    expect(document.body.textContent).not.toContain('leak-source')
    expect(document.body.textContent).not.toContain('leak-details')
    expect(document.body.textContent).not.toContain('99')
    expect(get).toHaveBeenCalledWith('/submissions/public', { params: { page: 1, page_size: 20 } })
  })
})
