import { describe, expect, it } from 'vitest'
import { validateProblem } from '../src/utils/problem-validation'

const valid = () => ({ title: 'A+B', statement: '题面', input: '', output: '', difficulty: 'easy' as const, time_limit_ms: 1000, published: false, tags: [], test_cases: [{ input: '1 2', output: '3', is_sample: true }] })

describe('管理员题目校验', () => {
  it('限制测试点数量为 50', () => {
    const payload = valid()
    payload.test_cases = Array.from({ length: 51 }, () => ({ input: '', output: '', is_sample: false }))
    expect(validateProblem(payload).test_cases).toContain('最多 50 个测试点')
  })

  it('输入和输出分别限制 256 KiB', () => {
    const payload = valid()
    payload.test_cases[0].input = '测'.repeat(90_000)
    expect(validateProblem(payload).test_cases).toContain('第 1 个测试点的输入超过 256 KiB')
  })

  it('时间限制必须在 100 到 5000 毫秒', () => {
    const payload = valid()
    payload.time_limit_ms = 99
    expect(validateProblem(payload).time_limit_ms).toBe('时间限制需为 100–5000 毫秒')
  })
})
