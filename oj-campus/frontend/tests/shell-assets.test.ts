import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('应用外壳静态资源', () => {
  it('sticky 顶栏使用完全不透明的暖色背景', () => {
    const styles = readFileSync(resolve(process.cwd(), 'src/styles.css'), 'utf8')
    const headerRule = styles.match(/\.site-header\s*\{([^}]*)\}/)?.[1] ?? ''
    expect(headerRule).toMatch(/background:\s*var\(--bg\)/)
    expect(headerRule).not.toContain('rgba(')
  })

  it('HTML 声明内嵌 favicon，fresh page 不会额外请求缺失的 favicon.ico', () => {
    const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf8')
    expect(html).toMatch(/<link\s+rel="icon"\s+href="data:image\/svg\+xml,/)
  })

  it('标签表格在窄屏解除全局最小宽度并把每行排成完整卡片', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/views/admin/AdminTagsView.vue'), 'utf8')
    expect(source).toContain('<table class="tag-table">')
    expect(source).toMatch(/@media \(max-width: 720px\)[\s\S]*\.tag-list-card \.table-wrap \{ overflow: visible; \}/)
    expect(source).toMatch(/@media \(max-width: 720px\)[\s\S]*\.tag-table \{ min-width: 0; display: block; \}/)
    expect(source).toMatch(/@media \(max-width: 720px\)[\s\S]*\.tag-table tr \{ display: grid;/)
    expect(source).toMatch(/@media \(max-width: 720px\)[\s\S]*\.tag-table \.tag-name-form label \{ overflow-wrap: anywhere; \}/)
    expect(source).toMatch(/@media \(max-width: 720px\)[\s\S]*\.tag-table td > \.button \{ width: 100%; \}/)
  })
})
