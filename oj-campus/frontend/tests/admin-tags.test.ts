import { fireEvent, render, screen, waitFor } from '@testing-library/vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../src/api/client'
import AdminTagsView from '../src/views/admin/AdminTagsView.vue'

afterEach(() => vi.restoreAllMocks())

describe('管理员标签管理', () => {
  it('显示加载状态，加载失败后可重试并恢复标签列表', async () => {
    let rejectLoad: (cause: Error) => void = () => undefined
    const get = vi.spyOn(api, 'get')
      .mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectLoad = reject }))
      .mockResolvedValueOnce({ data: [{ id: 1, name: 'math' }] })
    render(AdminTagsView)
    expect(screen.getByRole('status').textContent).toContain('正在加载标签')
    rejectLoad(new Error('offline'))
    expect((await screen.findByRole('alert')).textContent).toContain('标签加载失败')
    await fireEvent.click(screen.getByRole('button', { name: '重新加载标签' }))
    expect(await screen.findByLabelText('重命名标签 math')).toBeTruthy()
    expect(get).toHaveBeenCalledTimes(2)
  })

  it('加载现有标签并创建新标签，提供成功反馈', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 1, name: 'math' }] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { id: 2, name: 'graphs' } })
    render(AdminTagsView)
    expect(await screen.findByLabelText('重命名标签 math')).toBeTruthy()
    expect(api.get).toHaveBeenCalledWith('/admin/tags')
    await fireEvent.update(screen.getByLabelText('新标签名称'), ' graphs ')
    await fireEvent.click(screen.getByRole('button', { name: '创建标签' }))
    expect(await screen.findByLabelText('重命名标签 graphs')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('标签“graphs”已创建')
    expect(post).toHaveBeenCalledWith('/admin/tags', { name: 'graphs' })
  })

  it('重命名标签并在列表中显示后端返回的新名称', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 1, name: 'math' }] })
    const patch = vi.spyOn(api, 'patch').mockResolvedValue({ data: { id: 1, name: 'algorithms' } })
    render(AdminTagsView)
    const name = await screen.findByLabelText('重命名标签 math')
    await fireEvent.update(name, ' algorithms ')
    await fireEvent.click(screen.getByRole('button', { name: '保存标签 math' }))
    expect(await screen.findByLabelText('重命名标签 algorithms')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('标签已重命名为“algorithms”')
    expect(patch).toHaveBeenCalledWith('/admin/tags/1', { name: 'algorithms' })
  })

  it('确认后删除标签并保留成功反馈', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 2, name: 'graphs' }] })
    const remove = vi.spyOn(api, 'delete').mockResolvedValue({ data: undefined })
    render(AdminTagsView)
    await screen.findByLabelText('重命名标签 graphs')
    await fireEvent.click(screen.getByRole('button', { name: '删除标签 graphs' }))
    await waitFor(() => expect(screen.queryByLabelText('重命名标签 graphs')).toBeNull())
    expect(screen.getByRole('status').textContent).toContain('标签“graphs”已删除')
    expect(remove).toHaveBeenCalledWith('/admin/tags/2')
  })

  it('删除被题目占用的标签时保留列表并可直接重试', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 1, name: 'math' }] })
    const inUse = { isAxiosError: true, response: { data: { code: 'tag_in_use', message: 'Tag is assigned to a problem' } } }
    const remove = vi.spyOn(api, 'delete').mockRejectedValueOnce(inUse).mockResolvedValueOnce({ data: undefined })
    render(AdminTagsView)
    await screen.findByLabelText('重命名标签 math')
    await fireEvent.click(screen.getByRole('button', { name: '删除标签 math' }))
    expect((await screen.findByRole('alert')).textContent).toContain('该标签仍被题目使用')
    expect(screen.getByLabelText('重命名标签 math')).toBeTruthy()
    await fireEvent.click(screen.getByRole('button', { name: '重试删除标签 math' }))
    await waitFor(() => expect(screen.queryByLabelText('重命名标签 math')).toBeNull())
    expect(remove).toHaveBeenCalledTimes(2)
  })

  it('最长 64 字符标签仍保留完整可访问的重命名与删除控件', async () => {
    const longName = 'a'.repeat(64)
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 9, name: longName }] })
    render(AdminTagsView)
    expect(await screen.findByLabelText(`重命名标签 ${longName}`)).toBeTruthy()
    expect(screen.getByRole('button', { name: `保存标签 ${longName}` })).toBeTruthy()
    expect(screen.getByRole('button', { name: `删除标签 ${longName}` })).toBeTruthy()
  })
})
