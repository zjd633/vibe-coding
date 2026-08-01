import axios, { AxiosError } from 'axios'
import type { ApiErrorBody } from '../types'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

const errorMap: Record<string, string> = {
  authentication_required: '登录状态已失效，请重新登录',
  invalid_credentials: '用户名或密码不正确',
  username_taken: '用户名已被使用',
  email_taken: '邮箱已被使用',
  forbidden: '你没有权限执行此操作',
  not_found: '请求的内容不存在',
  outstanding_limit: '最多只能有 3 次提交等待评测，请稍后再试',
  invalid_tag: '选择的标签不存在或已被删除，请重新选择',
  tag_taken: '该标签已存在，请使用已有标签',
  tag_in_use: '该标签仍被题目使用，暂时无法删除',
  conflict: '数据发生冲突，请刷新后重试',
  registration_conflict: '注册信息与现有账户冲突，请检查后重试',
  validation_error: '请检查填写内容',
  internal_error: '服务器开小差了，请稍后重试',
}

export function readableError(error: unknown, fallback = '操作失败，请重试'): string {
  if (!axios.isAxiosError(error)) return fallback
  const body = (error as AxiosError<ApiErrorBody>).response?.data
  return body ? errorMap[body.code] ?? body.message ?? fallback : '网络连接失败，请检查连接后重试'
}

export function fieldErrors(error: unknown): Record<string, string> {
  if (!axios.isAxiosError(error)) return {}
  return (error as AxiosError<ApiErrorBody>).response?.data?.field_errors ?? {}
}
