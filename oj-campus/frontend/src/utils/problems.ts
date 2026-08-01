import type { Difficulty } from '../types'

export interface ProblemFilters {
  keyword: string
  difficulty: '' | Difficulty
  tag: string
  solved: '' | boolean
  page: number
}

export function buildProblemParams(filters: ProblemFilters) {
  const params: Record<string, string | boolean | number> = { page: filters.page, page_size: 20 }
  const keyword = filters.keyword.trim()
  if (keyword) params.keyword = keyword
  if (filters.difficulty) params.difficulty = filters.difficulty
  if (filters.tag) params.tag = filters.tag.trim().toLowerCase()
  if (typeof filters.solved === 'boolean') params.solved = filters.solved
  return params
}

const difficultyLabels: Record<Difficulty, string> = {
  easy: '简单 · 1 星',
  medium: '中等 · 2 星',
  hard: '困难 · 3 星',
}

export const difficultyLabel = (difficulty: Difficulty) => difficultyLabels[difficulty]
