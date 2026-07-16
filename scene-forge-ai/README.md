# SceneForge AI

SceneForge AI 是根据 Bilibili 演示视频独立复刻的节点式 AI 漫剧创作工作台。项目没有使用原软件源码、品牌或私有接口；默认提供可离线体验的演示模式，也可通过本地代理接入 OpenAI-compatible 图片生成服务。

## 已实现

- 项目管理页与本地项目入口
- 可平移、缩放、拖拽、连线并自动保存的无限节点画布
- AI 图片、角色素材、VR360、3D 导演、分镜生成、分镜输出六类节点
- 本地稳定生图演示，以及可选的服务端 API 代理
- 本地全景图片导入和单图导出
- Three.js 全屏 3D 导演：
  - 红/绿/蓝角色
  - 沙发、桌子、椅子、墙体、灯光、几何体
  - 对象选择、位置、旋转、缩放
  - 正面、侧面、俯视、广角、近景镜头
  - 彩色视角图和深度图导出
- 375px 到桌面宽度的响应式布局、键盘焦点、减少动画偏好和无障碍标签

## 启动

需要 Node.js 22.12 或更高版本。

```powershell
npm install
npm run dev
```

打开 [http://127.0.0.1:5173](http://127.0.0.1:5173)。默认处于 `DEMO` 模式，不需要任何密钥。

只启动前端：

```powershell
npm run dev:web
```

## 接入图片 API

复制 `.env.example` 为 `.env`，配置完整的图片生成接口地址：

```dotenv
IMAGE_API_URL=https://api.example.com/v1/images/generations
IMAGE_API_KEY=replace-me
IMAGE_MODEL=gpt-image-1
API_PORT=8787
```

随后运行 `npm run dev`，在右上角设置中选择 `OpenAI-compatible API`。密钥只由本地 Node 代理读取，不写入浏览器 localStorage。

代理会向上游发送 `model`、`prompt`、`n` 和 `size`，并兼容返回 `url` 或 `b64_json` 的常见 Images API 响应。不同供应商若使用其他字段，可在 `server/index.mjs` 中调整映射。

## 验证

```powershell
npm test
npm run typecheck
npm run build
```

当前单元/组件测试覆盖工作流持久化、分镜解析、演示/API 生图、项目导航、六类节点、全景导入、导演状态、全屏模态层和设置校验。真实浏览器 QA 截图位于 `output/playwright/.playwright-cli/`。

## 目录

```text
src/
├── components/          项目页、编辑器、节点、设置和 3D 导演
├── domain/              工作流与导演的纯状态逻辑
├── lib/                 演示图片与图片生成客户端
└── styles.css           设计令牌和响应式视觉系统
server/index.mjs         OpenAI-compatible 本地代理
docs/plans/              设计说明与实施计划
reference-subtitles/     从参考视频提取的字幕证据
```

## 参考

- [Bilibili：AI漫剧彻底变了：最强工具免费上线（稳定出片）](https://www.bilibili.com/video/BV1kbQbB2Ew1)

本项目仅用于界面与交互复刻练习；示例画面均为代码生成的原创占位视觉。
