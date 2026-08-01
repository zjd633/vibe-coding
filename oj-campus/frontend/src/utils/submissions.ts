import type { SubmissionStatus } from '../types'

export const verdictLabel: Record<SubmissionStatus, string> = {
  PENDING: '等待评测', JUDGING: '评测中', AC: '答案正确', WA: '答案错误', CE: '编译错误', RE: '运行错误', TLE: '超出时间限制', OLE: '输出超过限制', SE: '评测系统错误',
}

export const isPending = (status: SubmissionStatus) => status === 'PENDING' || status === 'JUDGING'

export function safeDiagnostic(submission: { status: SubmissionStatus; details?: string | null }) {
  if (submission.status === 'AC') return '本次提交已通过全部测试点。'
  if (submission.details) return submission.details
  return '评测未通过，请检查算法、边界条件和输入输出格式。'
}
