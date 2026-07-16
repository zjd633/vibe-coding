export type DirectorItemType = 'actor' | 'prop'
export type DirectorItemKind = 'actor' | 'sofa' | 'table' | 'chair' | 'wall' | 'lamp' | 'cube'
export type CameraPresetId = 'front' | 'side' | 'overhead' | 'wide' | 'close'

export interface DirectorItem {
  id: string
  type: DirectorItemType
  kind: DirectorItemKind
  name: string
  color: string
  position: [number, number, number]
  rotation: [number, number, number]
  scale: number
}

export interface DirectorState {
  items: DirectorItem[]
  selectedId: string | null
}

export interface CameraPreset {
  label: string
  position: [number, number, number]
  target: [number, number, number]
}

export const cameraPresets: Record<CameraPresetId, CameraPreset> = {
  front: { label: '正面', position: [0, 3, 9], target: [0, 1, 0] },
  side: { label: '侧面', position: [9, 3, 0], target: [0, 1, 0] },
  overhead: { label: '俯视', position: [0, 11, 0.01], target: [0, 0, 0] },
  wide: { label: '广角', position: [8, 5, 11], target: [0, 1, 0] },
  close: { label: '近景', position: [2.5, 2.2, 4.5], target: [0, 1.35, 0] },
}

const kindLabels: Record<DirectorItemKind, string> = {
  actor: '角色',
  sofa: '沙发',
  table: '桌子',
  chair: '椅子',
  wall: '墙体',
  lamp: '灯光',
  cube: '几何体',
}

export function createDirectorState(): DirectorState {
  return {
    selectedId: 'actor-red-1',
    items: [
      {
        id: 'actor-red-1',
        type: 'actor',
        kind: 'actor',
        name: '红色角色 1',
        color: '#ef5545',
        position: [-1.5, 0, 0],
        rotation: [0, 0.15, 0],
        scale: 1,
      },
      {
        id: 'actor-green-1',
        type: 'actor',
        kind: 'actor',
        name: '绿色角色 1',
        color: '#31cf91',
        position: [1.5, 0, -0.4],
        rotation: [0, -0.2, 0],
        scale: 1,
      },
    ],
  }
}

export function selectDirectorItem(state: DirectorState, selectedId: string | null): DirectorState {
  return { ...state, selectedId }
}

export function addDirectorItem(
  state: DirectorState,
  type: DirectorItemType,
  kind: DirectorItemKind,
  color?: string,
): DirectorState {
  const existing = state.items.filter((item) => item.kind === kind).length
  const number = existing + 1
  const id = `${kind}-${number}-${state.items.length + 1}`
  const item: DirectorItem = {
    id,
    type,
    kind,
    name: `${kindLabels[kind]} ${number}`,
    color: color || (type === 'actor' ? '#4d9aff' : '#c39155'),
    position: [((state.items.length % 4) - 1.5) * 1.4, 0, -Math.floor(state.items.length / 4) * 1.2],
    rotation: [0, 0, 0],
    scale: 1,
  }
  return { items: [...state.items, item], selectedId: item.id }
}

export function updateDirectorItem(
  state: DirectorState,
  itemId: string,
  patch: Partial<Pick<DirectorItem, 'position' | 'rotation' | 'scale' | 'color' | 'name'>>,
): DirectorState {
  return {
    ...state,
    items: state.items.map((item) => (item.id === itemId ? { ...item, ...patch } : item)),
  }
}

export function removeDirectorItem(state: DirectorState, itemId: string): DirectorState {
  const items = state.items.filter((item) => item.id !== itemId)
  return {
    items,
    selectedId: state.selectedId === itemId ? (items[0]?.id ?? null) : state.selectedId,
  }
}
