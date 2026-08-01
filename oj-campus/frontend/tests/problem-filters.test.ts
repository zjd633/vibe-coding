import { describe, expect, it } from 'vitest'
import { buildProblemParams, difficultyLabel } from '../src/utils/problems'

describe('题目筛选', () => {
  it('只发送有意义的筛选参数并保留 solved=false', () => {
    expect(buildProblemParams({ keyword: '  数组 ', difficulty: '', tag: '', solved: false, page: 2 })).toEqual({ keyword: '数组', solved: false, page: 2, page_size: 20 })
  })

  it('难度标签始终同时包含文字和星级', () => {
    expect(difficultyLabel('easy')).toBe('简单 · 1 星')
    expect(difficultyLabel('medium')).toBe('中等 · 2 星')
    expect(difficultyLabel('hard')).toBe('困难 · 3 星')
  })
})
