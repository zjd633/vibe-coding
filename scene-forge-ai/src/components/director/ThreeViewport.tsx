import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  cameraPresets,
  type CameraPresetId,
  type DirectorItem,
} from '../../domain/director'

export interface DirectorExporter {
  exportColor: () => void
  exportDepth: () => void
}

interface ThreeViewportProps {
  items: DirectorItem[]
  selectedId: string | null
  cameraPreset: CameraPresetId
  onSelect: (itemId: string) => void
  onExporter: (exporter: DirectorExporter | null) => void
}

function makeMaterial(color: string, selected: boolean) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.65,
    metalness: 0.05,
    emissive: selected ? new THREE.Color(color).multiplyScalar(0.18) : new THREE.Color(0x000000),
  })
}

function markItem(object: THREE.Object3D, itemId: string) {
  object.traverse((child) => {
    child.userData.itemId = itemId
  })
}

function createActor(item: DirectorItem, selected: boolean): THREE.Group {
  const group = new THREE.Group()
  const material = makeMaterial(item.color, selected)
  const dark = makeMaterial('#12161d', false)

  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.92, 5, 10), material)
  body.position.y = 1.08
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.25, 20, 14), material)
  head.position.y = 1.92
  const leftLeg = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.62, 4, 8), dark)
  leftLeg.position.set(-0.11, 0.37, 0)
  const rightLeg = leftLeg.clone()
  rightLeg.position.x = 0.11
  const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.065, 0.62, 4, 8), material)
  leftArm.position.set(-0.36, 1.2, 0)
  leftArm.rotation.z = -0.08
  const rightArm = leftArm.clone()
  rightArm.position.x = 0.36
  rightArm.rotation.z = 0.08
  group.add(body, head, leftLeg, rightLeg, leftArm, rightArm)
  markItem(group, item.id)
  return group
}

function createProp(item: DirectorItem, selected: boolean): THREE.Group {
  const group = new THREE.Group()
  const material = makeMaterial(item.color, selected)
  const dark = makeMaterial('#6f4b2d', selected)
  const box = (width: number, height: number, depth: number, x = 0, y = height / 2, z = 0) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material)
    mesh.position.set(x, y, z)
    mesh.castShadow = true
    mesh.receiveShadow = true
    return mesh
  }

  if (item.kind === 'sofa') {
    group.add(box(2.4, 0.5, 0.85, 0, 0.35, 0), box(2.4, 0.9, 0.3, 0, 0.85, 0.34))
    group.add(box(0.25, 0.55, 0.85, -1.08, 0.55, 0), box(0.25, 0.55, 0.85, 1.08, 0.55, 0))
  } else if (item.kind === 'table') {
    group.add(box(2.2, 0.16, 1.05, 0, 1.05, 0))
    for (const x of [-0.86, 0.86]) for (const z of [-0.34, 0.34]) group.add(box(0.13, 1, 0.13, x, 0.5, z))
  } else if (item.kind === 'chair') {
    group.add(box(0.85, 0.14, 0.85, 0, 0.62, 0), box(0.85, 1.05, 0.13, 0, 1.16, 0.36))
    for (const x of [-0.31, 0.31]) for (const z of [-0.31, 0.31]) group.add(box(0.1, 0.58, 0.1, x, 0.29, z))
  } else if (item.kind === 'wall') {
    group.add(box(3.2, 2.6, 0.18, 0, 1.3, 0))
  } else if (item.kind === 'lamp') {
    const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 2.4), dark)
    stand.position.y = 1.2
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.25, 16, 10), material)
    bulb.position.y = 2.35
    const light = new THREE.PointLight(item.color, 2.5, 7)
    light.position.y = 2.35
    group.add(stand, bulb, light)
  } else {
    group.add(box(1, 1, 1))
  }

  markItem(group, item.id)
  return group
}

function downloadCanvas(canvas: HTMLCanvasElement, filename: string) {
  const link = document.createElement('a')
  link.download = filename
  link.href = canvas.toDataURL('image/png')
  link.click()
}

export default function ThreeViewport({
  items,
  selectedId,
  cameraPreset,
  onSelect,
  onExporter,
}: ThreeViewportProps) {
  const hostRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)
  const itemsGroupRef = useRef<THREE.Group | null>(null)
  const [supported] = useState(() => typeof window !== 'undefined' && 'WebGLRenderingContext' in window)

  useEffect(() => {
    if (!supported || !hostRef.current) return
    const host = hostRef.current
    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#07090d')
    scene.fog = new THREE.Fog('#07090d', 13, 32)
    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100)
    camera.position.set(...cameraPresets.wide.position)
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFShadowMap
    renderer.outputColorSpace = THREE.SRGBColorSpace
    host.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.08
    controls.maxPolarAngle = Math.PI * 0.49
    controls.minDistance = 2.5
    controls.maxDistance = 25
    controls.target.set(0, 1, 0)

    scene.add(new THREE.HemisphereLight(0xbfe7ff, 0x1b1822, 2.2))
    const keyLight = new THREE.DirectionalLight(0xffffff, 3.4)
    keyLight.position.set(4, 8, 5)
    keyLight.castShadow = true
    keyLight.shadow.mapSize.set(1024, 1024)
    scene.add(keyLight)
    const rim = new THREE.PointLight(0x28d7f3, 20, 18)
    rim.position.set(-6, 3, -4)
    scene.add(rim)

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 60),
      new THREE.MeshStandardMaterial({ color: '#0b0f15', roughness: 0.9 }),
    )
    floor.rotation.x = -Math.PI / 2
    floor.receiveShadow = true
    scene.add(floor)
    const grid = new THREE.GridHelper(60, 60, 0x344355, 0x1b2430)
    grid.position.y = 0.002
    scene.add(grid)
    const itemGroup = new THREE.Group()
    scene.add(itemGroup)

    sceneRef.current = scene
    cameraRef.current = camera
    rendererRef.current = renderer
    controlsRef.current = controls
    itemsGroupRef.current = itemGroup

    const resize = () => {
      const width = Math.max(host.clientWidth, 1)
      const height = Math.max(host.clientHeight, 1)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height, false)
    }
    const observer = new ResizeObserver(resize)
    observer.observe(host)
    resize()

    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    const selectFromPointer = (event: PointerEvent) => {
      const bounds = renderer.domElement.getBoundingClientRect()
      pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1
      pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1
      raycaster.setFromCamera(pointer, camera)
      const hit = raycaster.intersectObjects(itemGroup.children, true)[0]
      const itemId = hit?.object.userData.itemId as string | undefined
      if (itemId) onSelect(itemId)
    }
    renderer.domElement.addEventListener('pointerdown', selectFromPointer)

    let animationFrame = 0
    const render = () => {
      controls.update()
      renderer.render(scene, camera)
      animationFrame = requestAnimationFrame(render)
    }
    render()

    onExporter({
      exportColor: () => {
        renderer.render(scene, camera)
        downloadCanvas(renderer.domElement, 'sceneforge-camera-view.png')
      },
      exportDepth: () => {
        const previous = scene.overrideMaterial
        scene.overrideMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.BasicDepthPacking })
        renderer.render(scene, camera)
        downloadCanvas(renderer.domElement, 'sceneforge-depth-map.png')
        scene.overrideMaterial = previous
        renderer.render(scene, camera)
      },
    })

    return () => {
      onExporter(null)
      cancelAnimationFrame(animationFrame)
      observer.disconnect()
      renderer.domElement.removeEventListener('pointerdown', selectFromPointer)
      controls.dispose()
      renderer.dispose()
      host.removeChild(renderer.domElement)
    }
  }, [onExporter, onSelect, supported])

  useEffect(() => {
    const group = itemsGroupRef.current
    if (!group) return
    while (group.children.length) {
      const child = group.children.pop()!
      child.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose()
          if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose())
          else object.material.dispose()
        }
      })
    }
    items.forEach((item) => {
      const object = item.type === 'actor' ? createActor(item, item.id === selectedId) : createProp(item, item.id === selectedId)
      object.position.set(...item.position)
      object.rotation.set(...item.rotation)
      object.scale.setScalar(item.scale)
      group.add(object)
    })
  }, [items, selectedId])

  useEffect(() => {
    const camera = cameraRef.current
    const controls = controlsRef.current
    if (!camera || !controls) return
    const preset = cameraPresets[cameraPreset]
    camera.position.set(...preset.position)
    controls.target.set(...preset.target)
    controls.update()
  }, [cameraPreset])

  return (
    <div className="three-viewport" ref={hostRef}>
      {!supported && (
        <div className="three-fallback" aria-label="3D 预览占位">
          <div className="three-fallback-grid" />
          <span className="three-fallback-actor red" />
          <span className="three-fallback-actor green" />
          <p>浏览器 WebGL 启用后显示实时 3D 场景</p>
        </div>
      )}
    </div>
  )
}
