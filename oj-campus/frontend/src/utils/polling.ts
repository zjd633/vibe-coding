const terminalStates = new Set(['AC', 'WA', 'CE', 'RE', 'TLE', 'OLE', 'SE'])

export function startSubmissionPolling<T extends { status: string }>(fetcher: () => Promise<T>, onUpdate: (value: T) => void, onError?: (cause: unknown) => void) {
  let stopped = false
  let timer: ReturnType<typeof setTimeout> | undefined

  const tick = async () => {
    if (stopped) return
    try {
      const value = await fetcher()
      if (stopped) return
      onUpdate(value)
      if (terminalStates.has(value.status)) {
        stopped = true
        return
      }
    } catch (cause) {
      if (stopped) return
      stopped = true
      onError?.(cause)
    } finally {
      if (!stopped) timer = setTimeout(tick, 1000)
    }
  }

  timer = setTimeout(tick, 1000)
  return () => {
    stopped = true
    if (timer) clearTimeout(timer)
  }
}
