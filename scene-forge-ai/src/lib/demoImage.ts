const palettes = [
  ['#06141f', '#0f6070', '#e19c58'],
  ['#160c28', '#5145b5', '#ee6f8c'],
  ['#071d18', '#237a57', '#d6b268'],
  ['#1b1210', '#8c3f2f', '#f2b56b'],
] as const

function hashText(value: string): number {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function escapeXml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

export function createDemoImage(
  prompt: string,
  frameIndex = 0,
  width = 1024,
  height = 576,
): string {
  const seed = hashText(`${prompt}:${frameIndex}`)
  const palette = palettes[seed % palettes.length]
  const horizon = Math.round(height * (0.48 + ((seed >> 4) % 16) / 100))
  const moonX = Math.round(width * (0.18 + ((seed >> 8) % 58) / 100))
  const moonY = Math.round(height * (0.14 + ((seed >> 12) % 18) / 100))
  const safePrompt = escapeXml(prompt.trim() || '未命名镜头')
  const frameLabel = String(frameIndex + 1).padStart(2, '0')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${safePrompt}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${palette[0]}"/><stop offset="1" stop-color="${palette[1]}"/></linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${palette[1]}"/><stop offset="1" stop-color="${palette[0]}"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="14"/></filter>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#sky)"/>
  <circle cx="${moonX}" cy="${moonY}" r="${Math.max(22, width / 30)}" fill="${palette[2]}" opacity=".28" filter="url(#glow)"/>
  <circle cx="${moonX}" cy="${moonY}" r="${Math.max(13, width / 45)}" fill="#ffe8b2" opacity=".9"/>
  <path d="M0 ${horizon} Q ${width * 0.2} ${horizon - 90} ${width * 0.38} ${horizon - 20} T ${width * 0.7} ${horizon - 45} T ${width} ${horizon - 10} V${height}H0Z" fill="#07100f" opacity=".92"/>
  <rect y="${horizon}" width="${width}" height="${height - horizon}" fill="url(#water)" opacity=".72"/>
  <path d="M${width * 0.08} ${horizon + 28} H${width * 0.92} M${width * 0.18} ${horizon + 70} H${width * 0.78} M${width * 0.3} ${horizon + 115} H${width * 0.68}" stroke="#d6f7f3" stroke-opacity=".2" stroke-width="3"/>
  <g fill="${palette[2]}" opacity=".85">
    <rect x="${width * 0.6}" y="${horizon - 85}" width="${width * 0.2}" height="75" rx="3"/>
    <path d="M${width * 0.57} ${horizon - 85} L${width * 0.7} ${horizon - 135} L${width * 0.83} ${horizon - 85}Z"/>
    <rect x="${width * 0.63}" y="${horizon - 60}" width="12" height="50" fill="#101315"/>
    <rect x="${width * 0.76}" y="${horizon - 60}" width="12" height="50" fill="#101315"/>
  </g>
  <rect x="24" y="24" width="58" height="32" rx="16" fill="#05070a" fill-opacity=".65" stroke="#fff" stroke-opacity=".2"/>
  <text x="53" y="46" fill="#fff" font-family="Inter, sans-serif" font-size="14" text-anchor="middle">F${frameLabel}</text>
  <rect x="24" y="${height - 82}" width="${Math.min(width - 48, 560)}" height="58" rx="12" fill="#05070a" fill-opacity=".72"/>
  <text x="44" y="${height - 48}" fill="#fff" font-family="Inter, Noto Sans SC, sans-serif" font-size="${Math.max(15, width / 54)}">${safePrompt.slice(0, 32)}</text>
</svg>`

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}
