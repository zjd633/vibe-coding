import type { ProblemPayload } from '../types'

export function validateProblem(problem: ProblemPayload) {
  const errors: Record<string, string> = {}
  if (!problem.title.trim()) errors.title = '请输入题目名称'
  if (problem.title.length > 200) errors.title = '题目名称最多 200 个字符'
  if (!problem.statement.trim()) errors.statement = '请输入题目描述'
  if (problem.time_limit_ms < 100 || problem.time_limit_ms > 5000) errors.time_limit_ms = '时间限制需为 100–5000 毫秒'
  if (problem.test_cases.length > 50) errors.test_cases = '最多 50 个测试点'
  const encoder = new TextEncoder()
  problem.test_cases.forEach((item, index) => {
    if (encoder.encode(item.input).byteLength > 256 * 1024) errors.test_cases = `第 ${index + 1} 个测试点的输入超过 256 KiB`
    if (encoder.encode(item.output).byteLength > 256 * 1024) errors.test_cases = `第 ${index + 1} 个测试点的输出超过 256 KiB`
  })
  return errors
}
