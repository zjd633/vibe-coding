# SceneForge AI Clone Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a high-fidelity, runnable web clone of the reference video's node-based AI storyboard workspace with a functional fullscreen 3D director and demo/API generation modes.

**Architecture:** A Vite React client owns the node graph and local persistence. A small Express-compatible Node server proxies optional OpenAI-compatible image requests, while deterministic browser-generated SVG scenes keep the app fully usable without credentials. Three.js powers the director viewport and exports.

**Tech Stack:** React 19, TypeScript, Vite, `@xyflow/react`, Three.js, Lucide React, Vitest, Testing Library, Playwright, Node HTTP server.

---

### Task 1: Project shell and state contracts

**Files:**
- Create: `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`
- Create: `src/domain/workflow.ts`
- Test: `src/domain/workflow.test.ts`

1. Create the package/tooling configuration.
2. Write failing tests for default workflow creation, scene splitting, and local persistence serialization.
3. Run `npm test -- src/domain/workflow.test.ts` and confirm failures are caused by missing exports.
4. Implement minimal typed workflow helpers and rerun the test to green.

### Task 2: Demo image generator and API client

**Files:**
- Create: `src/lib/demoImage.ts`, `src/lib/generateImage.ts`
- Create: `server/index.mjs`, `.env.example`
- Test: `src/lib/demoImage.test.ts`, `src/lib/generateImage.test.ts`

1. Write failing tests that require deterministic safe SVG data URLs and demo/API mode routing.
2. Run the focused tests and verify expected assertion failures.
3. Implement the generator and client, then create the server proxy with environment-only API credentials.
4. Run focused and full unit tests.

### Task 3: Project manager and editor shell

**Files:**
- Create: `src/main.tsx`, `src/App.tsx`, `src/styles.css`
- Create: `src/components/ProjectHome.tsx`, `src/components/EditorShell.tsx`
- Test: `src/App.test.tsx`

1. Write a failing interaction test for opening a project and returning home.
2. Verify the failure, implement the two screens and navigation, then rerun to green.
3. Add the OLED semantic color tokens, responsive layout, focus states, reduced-motion handling and skip link.

### Task 4: Node canvas and custom nodes

**Files:**
- Create: `src/components/WorkflowCanvas.tsx`
- Create: `src/components/nodes/NodeFrame.tsx`
- Create: `src/components/nodes/ImagePromptNode.tsx`
- Create: `src/components/nodes/MediaNode.tsx`
- Create: `src/components/nodes/PanoramaNode.tsx`
- Create: `src/components/nodes/DirectorNode.tsx`
- Create: `src/components/nodes/StoryboardNode.tsx`
- Create: `src/components/nodes/StoryboardOutputNode.tsx`
- Test: `src/components/WorkflowCanvas.test.tsx`

1. Write failing tests for node type registration, prompt editing, and generation callbacks.
2. Verify red, implement the minimal React Flow canvas and nodes, then verify green.
3. Add connections, minimap/controls, node toolbar, selection styling and local autosave.

### Task 5: Fullscreen Three.js director

**Files:**
- Create: `src/components/director/DirectorModal.tsx`
- Create: `src/components/director/ThreeViewport.tsx`
- Create: `src/domain/director.ts`
- Test: `src/domain/director.test.ts`, `src/components/director/DirectorModal.test.tsx`

1. Write failing tests for actor/prop addition, transforms, camera presets and modal escape behavior.
2. Verify red, implement state helpers and accessible modal structure, then verify green.
3. Add the Three.js viewport, orbit controls, selection, color/depth export and responsive tool drawers.

### Task 6: Settings, feedback and persistence

**Files:**
- Create: `src/components/SettingsDialog.tsx`, `src/components/ToastRegion.tsx`
- Modify: `src/App.tsx`, `src/components/EditorShell.tsx`
- Test: `src/components/SettingsDialog.test.tsx`

1. Write failing tests for validated settings and save feedback.
2. Verify red, implement form labels/errors and local non-secret settings persistence, then verify green.
3. Wire loading, success and recoverable error states across generation actions.

### Task 7: Browser verification and documentation

**Files:**
- Create: `playwright.config.ts`, `e2e/app.spec.ts`, `README.md`

1. Write Playwright smoke checks for desktop project entry, fullscreen director, settings, and 375px overflow.
2. Run `npm run test:e2e` and fix only demonstrated failures.
3. Run `npm test`, `npm run typecheck`, and `npm run build`.
4. Start the production preview, capture screenshots, visually inspect them, and document commands/API setup in README.

The workspace is not currently a Git repository, so commit steps are intentionally omitted rather than creating repository history without user authorization.
