# OJ Campus

OJ Campus 是一个面向课堂练习的本地教学 OJ：仅题库练习、仅 C++17、学生与管理员两种角色。它使用 Vue 3 提供界面、FastAPI 提供 API、SQLite 保存数据，独立 Worker 负责判题。

> **安全警告（必须阅读）**：Windows 子进程执行**不是安全沙箱**。本项目只能运行受信任的本地教学代码，绝不能接收不受信任的代码，也绝不能部署到公网或作为多租户服务使用。

## 架构

```text
浏览器 ── Vite / FastAPI 静态构建 ──> FastAPI API ──> SQLite
                                         │
                                         └────> 独立 Judge Worker ──> g++ C++17
```

生产式静态回退会从 `frontend/dist` 提供 SPA；`/api/*` 永远保留给 API，不会被 HTML 回退覆盖。

## 快速开始

前置条件：Python 3.11+、Node.js 20+ / npm，以及 MinGW-w64 的 `g++.exe`。默认编译器为 `E:\mingw64\bin\g++.exe`，也可以通过 `OJ_GPP_PATH` 指定。

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

打开 <http://127.0.0.1:5173>。按 `Ctrl+C` 会停止 API、Worker 与 Vite 子进程。

测试、类型检查和生产构建：

```powershell
.\scripts\test.ps1
.\scripts\test.ps1 -E2E  # 另跑 Playwright；首次可先执行 cd frontend; npx playwright install chromium
```

每个脚本都提供 `-Help`。若 PowerShell 的执行策略阻止本地脚本，请在当前进程执行 `Set-ExecutionPolicy -Scope Process Bypass`，不要放宽系统范围的执行策略。

## 本地演示数据与账号

`setup.ps1` 会执行 `python -m app.seed`。内置目录共 100 道中文题，按 `40 简单`、`35 中等`、`25 困难` 形成难度递进的知识阶梯：简单题覆盖输入输出、分支、循环、基础数学、数组、字符串和简单模拟；中等题覆盖排序与二分、前缀和与双指针、栈队列与哈希、搜索、贪心和基础动态规划；困难题覆盖图论、进阶动态规划、回溯与综合搜索、并查集与堆等数据结构，以及综合算法与模拟。题库支持按难度和标签筛选；英文标签筛选不区分大小写，例如 `BFS` 与 `bfs` 等价，但不承诺对全部 Unicode 文本执行完整 casefold。

种子命令可重复执行，但它不是一般 upsert：正常情况下只插入目录中数据库尚缺少的 title。同 title 记录已经存在时，会保留该记录并跳过对应目录题，不覆盖题面、标签、测试点、revision 或管理员修改。管理员新建的题目也会保留，因此数据库总题数可以超过 100；如果管理员把内置题改名，下次执行种子无法用旧 ID 关联它，会保留改名后的记录并重新插入目录中的原标题。种子命令永不删除或合并管理员数据。

唯一允许更新的兼容例外是 `网格最小路径和` 的完整旧内置签名：revision 为 1，全部题面与输入输出 metadata、难度、published 状态、时间限制、精确标签以及两个按 position 排列的测试点都必须匹配，才会把隐藏答案从 `6` 改为 `5`、revision 从 1 增至 2。实现会修复所有完全匹配的候选；任一字段已编辑，或只是同名碰撞但不满足完整签名，都不会修复。

> **以下账号和密码仅用于本地演示，绝不能用于真实环境。**

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `demo_admin` | `ojcampus-demo` |
| 学生 | `demo_student` | `ojcampus-demo` |

## 环境变量

| 变量 | 用途 | 默认值 |
| --- | --- | --- |
| `OJ_DATABASE_URL` | SQLAlchemy SQLite URL | `backend/data/oj-campus.db` |
| `OJ_GPP_PATH` | `g++.exe` 的绝对路径 | `E:\mingw64\bin\g++.exe` |
| `OJ_FRONTEND_DIST` | FastAPI 静态 SPA 构建目录 | `frontend/dist` |

## API 概览

- `POST /api/auth/register`、`/login`、`/logout`：Cookie 会话认证；`GET /me` 查看当前账号，`GET /session` 供页面无错误地恢复可选会话。
- `GET /api/problems`、`GET /api/problems/{id}`：公开题库；详情只返回样例测试点。
- `POST /api/submissions`：学生提交 C++17；`GET /api/submissions/{id}` 仅所有者或管理员可见。
- `GET /api/dashboard`、`GET /api/leaderboard`：学习统计和排行榜。
- `/api/admin/*`：管理员题目、标签、用户与提交管理。管理员可见隐藏用例和内部诊断。

返回的评测状态包括：`PENDING`（等待评测）、`JUDGING`（评测中）、`AC`（正确）、`WA`（答案错误）、`CE`（编译错误）、`RE`（运行错误）、`TLE`（超时）、`OLE`（输出超限）和 `SE`（评测系统错误）。公开提交不会泄露源码、隐藏用例或内部诊断。

## 常见问题

- **找不到 g++**：安装 MinGW-w64，或设置 `$env:OJ_GPP_PATH='D:\path\to\g++.exe'` 后重新运行 `setup.ps1`。
- **端口 8000 / 5173 被占用**：结束旧的本地开发进程后重试；`dev.ps1` 的 Ctrl+C 清理会一并停止它启动的子进程。
- **页面提示 frontend build missing**：执行 `cd frontend; npm run build`，或将 `OJ_FRONTEND_DIST` 指向正确的构建目录。
- **Playwright 找不到浏览器**：在 `frontend` 目录执行 `npx playwright install chromium`，随后运行 `npx playwright test`。
- **数据库需要重置**：只在确认可丢弃本地演示数据后，删除 `backend/data/oj-campus.db`，然后重新运行 `setup.ps1`。不要对含有重要数据的数据库执行此操作。

## 开发说明

后端测试位于 `backend/tests`，前端单元测试位于 `frontend/tests`，端到端测试位于 `frontend/e2e`。Playwright 会创建独立、被 git 忽略的 `backend/data/playwright-e2e.db` 并在其上运行种子，避免污染默认演示数据库。
