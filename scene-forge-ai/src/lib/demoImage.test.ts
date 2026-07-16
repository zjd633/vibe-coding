import { describe, expect, it } from 'vitest'
import { createDemoImage } from './demoImage'

describe('createDemoImage', () => {
  it('creates a deterministic SVG data URL for the same prompt and index', () => {
    const first = createDemoImage('雨夜庭院', 2, 640, 360)
    const second = createDemoImage('雨夜庭院', 2, 640, 360)

    expect(first).toBe(second)
    expect(first).toMatch(/^data:image\/svg\+xml;charset=utf-8,/)
  })

  it('escapes prompt text before placing it in SVG markup', () => {
    const image = createDemoImage('<script>alert(1)</script>', 0, 640, 360)
    const svg = decodeURIComponent(image.split(',')[1])

    expect(svg).not.toContain('<script>')
    expect(svg).toContain('&lt;script&gt;')
  })

  it('changes the composition for a different frame index', () => {
    expect(createDemoImage('庭院', 0, 640, 360)).not.toBe(
      createDemoImage('庭院', 1, 640, 360),
    )
  })
})
