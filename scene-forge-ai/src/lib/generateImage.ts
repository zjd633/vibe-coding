import { createDemoImage } from './demoImage'

export interface GenerateImageRequest {
  mode: 'demo' | 'api'
  prompt: string
  count: number
  width: number
  height: number
  model?: string
}

type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>

export async function generateImages(
  request: GenerateImageRequest,
  fetcher: FetchLike = fetch,
): Promise<string[]> {
  if (request.mode === 'demo') {
    return Array.from({ length: request.count }, (_, index) =>
      createDemoImage(request.prompt, index, request.width, request.height),
    )
  }

  const response = await fetcher('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  const payload = (await response.json()) as { images?: string[]; error?: string }
  if (!response.ok || !payload.images) {
    throw new Error(payload.error || `图片生成失败（${response.status}）`)
  }
  return payload.images
}
