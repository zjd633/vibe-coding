export type Role = 'student' | 'admin'
export type Difficulty = 'easy' | 'medium' | 'hard'
export type SubmissionStatus = 'PENDING' | 'JUDGING' | 'AC' | 'WA' | 'CE' | 'RE' | 'TLE' | 'OLE' | 'SE'

export interface User {
  id: number
  username: string
  email: string
  display_name: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface TestCase {
  input: string
  output: string
  is_sample: boolean
  position?: number
}

export interface Tag {
  id: number
  name: string
}

export interface Problem {
  id: number
  title: string
  statement: string
  input: string
  output: string
  difficulty: Difficulty
  time_limit_ms: number
  published: boolean
  revision: number
  tags: string[]
  test_cases?: TestCase[]
  created_at?: string
  updated_at?: string
}

export interface ProblemPayload {
  title: string
  statement: string
  input: string
  output: string
  difficulty: Difficulty
  time_limit_ms: number
  published: boolean
  tags: string[]
  test_cases: TestCase[]
}

export interface Submission {
  id: number
  user_id: number
  problem_id: number
  problem_revision: number
  language: 'cpp17'
  status: SubmissionStatus
  runtime_ms: number | null
  failed_case?: number | null
  details?: string | null
  source?: string
  created_at: string
}

export interface PageResult<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}

export interface ApiErrorBody {
  code: string
  message: string
  field_errors?: Record<string, string>
}
