# ReplyKey 微信回复助手

ReplyKey 是一个仅面向 Windows 桌面微信的托盘工具。你先在微信里复制对方消息，再按全局热键，ReplyKey 会通过你配置的 Chat Completions 服务生成一条中文草稿，并在安全条件满足时粘贴到原微信输入框。

**它在任何情况下都不会自动发送消息，也不会注入 Enter。** 草稿进入输入框后仍可编辑，必须由你确认并手动发送。

## 使用便携版

1. 解压 `ReplyKey-portable.zip`，保持 `ReplyKey` 目录内的文件结构不变。
2. 双击 `ReplyKey.exe`。首次启动会显示隐私说明。
3. 打开托盘菜单中的“设置”，填写：
   - API Base URL；官方 OpenAI 默认为 `https://api.openai.com/v1`
   - API Key
   - 模型；默认 `gpt-5.6-luna`
   - 回复语气、回复长度和全局热键
4. 点击“测试连接”。这是一次真实、最小的 Chat Completions 请求，可能产生极少量 API 用量。
5. 在桌面微信中复制对方消息，保持原微信窗口位于前台，按 `Ctrl+Alt+R`。
6. 草稿进入输入框后检查、编辑，并由你手动发送。

如果生成期间切换了窗口，ReplyKey 不会抢回焦点，也不会向新窗口粘贴；草稿只会留在剪贴板中，并通过系统托盘提示。

## 支持范围

- Windows 10/11 x64
- 当前桌面微信进程 `Weixin.exe`
- 旧版桌面微信进程 `WeChat.exe`
- OpenAI Chat Completions API，或兼容 `POST /chat/completions` 且支持标准 `model + messages` 请求/响应结构的服务

默认模型来自 OpenAI 当前模型说明中的高吞吐选项：[Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)。Chat Completions 请求结构参考：[Create chat completion](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。

## 安全边界

- 不读取微信聊天数据库，不截图，不做 OCR，不识别联系人。
- 只有前台窗口属于 `Weixin.exe` 或 `WeChat.exe` 时才会读取剪贴板并准备请求。
- 同一时间只允许一个生成请求；忙碌或短时间重复触发不会再次调用 API。
- 粘贴前再次确认原窗口仍存活、仍为前台窗口。
- 按键注入固定为 `Ctrl+V` 的按下/释放序列，代码接口中没有发送能力。
- 成功粘贴后恢复触发前的文本剪贴板内容。
- API 失败不会修改剪贴板，也不会向会话追加失败记录。

## 数据与存储

- API Key：Windows 凭据存储（通过 `keyring`），不进入配置文件。
- 普通设置：`%APPDATA%\ReplyKey\config.json`。
- 会话：只在内存中保留最近 8 次成功交互；30 分钟无操作清空，退出后消失。
- 日志：`%APPDATA%\ReplyKey\logs\replykey.log`，只记录固定事件代码、状态和 HTTP 状态等元数据，不记录密钥、聊天原文或草稿内容。

完整说明见 [PRIVACY.md](PRIVACY.md)。

## 托盘菜单

- **设置**：配置服务、模型、回复偏好、热键和开机启动。
- **暂停热键**：保留托盘程序，但停止处理生成操作。
- **清空会话**：立即移除内存上下文。
- **开机启动**：写入当前用户的 Windows 启动项，不需要管理员权限。移动便携目录后，关闭再重新开启此项即可刷新路径。
- **退出**：注销热键、关闭后台请求执行器并退出。

## 常见提示

- “请先在桌面微信中复制”：当前前台窗口不是受支持的微信进程。
- “剪贴板中没有可回复的文字”：先复制一段文本消息。
- “正在生成”：已有请求进行中，本次触发不会调用 API。
- “API Key 无效或没有权限”：检查密钥、模型访问权限和兼容服务配置。
- “请求过于频繁或额度不足”：等待后重试，或检查服务额度。
- “窗口已切换”：回复已复制，但没有向任何窗口自动粘贴。
- “热键已被占用”：在设置中更换组合键。

## 开发与测试

需要 Python 3.11：

```powershell
py -V:Astral/CPython3.11.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

测试不需要真实 API Key。本地契约服务器覆盖成功、401、429、超时、空内容和异常响应。

## 构建便携版

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_portable.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_portable.ps1
```

输出：

- `dist\ReplyKey\ReplyKey.exe`（onedir 便携目录）
- `dist\ReplyKey-portable.zip`

PyInstaller 使用 onedir/windowed 模式，避免每次启动都先解压单文件包。构建方式参考 [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html)。

