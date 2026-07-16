import { describe, expect, it } from 'vitest'
import {
  createDefaultWorkflow,
  deserializeWorkflow,
  parseStoryboardPrompts,
  serializeWorkflow,
} from './workflow'

describe('workflow domain', () => {
  it('creates the six-node reference workflow with connected stages', () => {
    const workflow = createDefaultWorkflow()

    expect(workflow.nodes.map((node) => node.type)).toEqual([
      'media',
      'imagePrompt',
      'panorama',
      'director',
      'storyboard',
      'storyboardOutput',
    ])
    expect(workflow.edges).toHaveLength(6)
  })

  it('splits a multiline storyboard and removes blank lines', () => {
    expect(parseStoryboardPrompts('男主转身\n\n 女主追上来 \n雨中对话')).toEqual([
      '男主转身',
      '女主追上来',
      '雨中对话',
    ])
  })

  it('round-trips workflow state and falls back for invalid JSON', () => {
    const workflow = createDefaultWorkflow()
    expect(deserializeWorkflow(serializeWorkflow(workflow))).toEqual(workflow)
    expect(deserializeWorkflow('{broken')).toEqual(createDefaultWorkflow())
  })
})
