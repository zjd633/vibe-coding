import { describe, expect, it, vi } from 'vitest'
import { generateImages } from './generateImage'

describe('generateImages', () => {
  it('uses the local deterministic generator in demo mode', async () => {
    const request = vi.fn()
    const images = await generateImages(
      { mode: 'demo', prompt: '古风庭院', count: 2, width: 512, height: 512 },
      request,
    )

    expect(request).not.toHaveBeenCalled()
    expect(images).toHaveLength(2)
    expect(images.every((image) => image.startsWith('data:image/svg+xml'))).toBe(true)
  })

  it('posts API requests through the local proxy and returns its images', async () => {
    const request = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ images: ['https://example.com/frame.webp'] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const images = await generateImages(
      {
        mode: 'api',
        prompt: '雨夜庭院',
        count: 1,
        width: 1024,
        height: 576,
        model: 'image-model',
      },
      request,
    )

    expect(request).toHaveBeenCalledWith(
      '/api/generate',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(images).toEqual(['https://example.com/frame.webp'])
  })

  it('surfaces a recoverable proxy error message', async () => {
    const request = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: 'API 尚未配置' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(
      generateImages({ mode: 'api', prompt: '庭院', count: 1, width: 512, height: 512 }, request),
    ).rejects.toThrow('API 尚未配置')
  })
})
