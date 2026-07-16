import express from 'express'

const app = express()
const port = Number(process.env.API_PORT || 8787)

app.disable('x-powered-by')
app.use(express.json({ limit: '1mb' }))

app.get('/api/health', (_request, response) => {
  response.json({ ok: true, configured: Boolean(process.env.IMAGE_API_KEY) })
})

app.post('/api/generate', async (request, response) => {
  const endpoint = process.env.IMAGE_API_URL
  const apiKey = process.env.IMAGE_API_KEY
  const { prompt, count = 1, width = 1024, height = 1024, model } = request.body ?? {}

  if (!endpoint || !apiKey) {
    response.status(503).json({ error: 'API 尚未配置，请使用演示模式或设置服务端环境变量。' })
    return
  }
  if (typeof prompt !== 'string' || !prompt.trim()) {
    response.status(400).json({ error: '提示词不能为空。' })
    return
  }

  try {
    const upstream = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: model || process.env.IMAGE_MODEL || 'gpt-image-1',
        prompt: prompt.trim(),
        n: Math.max(1, Math.min(Number(count) || 1, 4)),
        size: `${Number(width) || 1024}x${Number(height) || 1024}`,
      }),
    })
    const payload = await upstream.json()
    if (!upstream.ok) {
      response.status(upstream.status).json({
        error: payload?.error?.message || payload?.message || '上游图片服务请求失败。',
      })
      return
    }

    const images = (payload?.data || [])
      .map((item) => item?.url || (item?.b64_json ? `data:image/png;base64,${item.b64_json}` : null))
      .filter(Boolean)
    if (!images.length) {
      response.status(502).json({ error: '上游服务没有返回可用图片。' })
      return
    }
    response.json({ images })
  } catch (error) {
    response.status(502).json({
      error: error instanceof Error ? error.message : '无法连接上游图片服务。',
    })
  }
})

app.listen(port, '127.0.0.1', () => {
  console.log(`SceneForge API proxy listening on http://127.0.0.1:${port}`)
})
