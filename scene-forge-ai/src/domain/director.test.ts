import { describe, expect, it } from 'vitest'
import {
  addDirectorItem,
  cameraPresets,
  createDirectorState,
  updateDirectorItem,
} from './director'

describe('director domain', () => {
  it('starts with two color-coded actors matching the reference workflow', () => {
    const state = createDirectorState()

    expect(state.items.filter((item) => item.type === 'actor')).toHaveLength(2)
    expect(state.items.map((item) => item.color)).toEqual(expect.arrayContaining(['#ef5545', '#31cf91']))
  })

  it('adds a prop, selects it, and updates its transform immutably', () => {
    const initial = createDirectorState()
    const withSofa = addDirectorItem(initial, 'prop', 'sofa')
    const sofa = withSofa.items.find((item) => item.kind === 'sofa')!
    const moved = updateDirectorItem(withSofa, sofa.id, { position: [2, 0.5, -1], scale: 1.5 })

    expect(withSofa.selectedId).toBe(sofa.id)
    expect(moved.items.find((item) => item.id === sofa.id)?.position).toEqual([2, 0.5, -1])
    expect(initial.items).not.toContain(sofa)
  })

  it('defines front, side, overhead, and cinematic camera presets', () => {
    expect(Object.keys(cameraPresets)).toEqual(['front', 'side', 'overhead', 'wide', 'close'])
    expect(cameraPresets.overhead.position[1]).toBeGreaterThan(cameraPresets.front.position[1])
  })
})
