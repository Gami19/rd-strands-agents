import type { StreamPayload } from '../types/chat'

export function streamMetaFromPayload(
  payload: StreamPayload,
): Partial<{ phase: string; agent: string }> | null {
  if (
    payload.type === 'done' ||
    payload.type === 'error' ||
    payload.type === 'handoff'
  )
    return null
  const phase = 'phase' in payload ? payload.phase : undefined
  const agent = 'agent' in payload ? payload.agent : undefined
  if (phase === undefined && agent === undefined) return null
  const out: Partial<{ phase: string; agent: string }> = {}
  if (phase !== undefined) out.phase = phase
  if (agent !== undefined) out.agent = agent
  return out
}

export function tryParseDataLine(line: string): StreamPayload | null {
  const t = line.trim()
  if (!t.startsWith('data:')) return null
  const raw = t.slice(5).trim()
  if (!raw) return null
  try {
    return JSON.parse(raw) as StreamPayload
  } catch {
    return null
  }
}

export function feedSseLines(
  buffer: string,
  chunk: string,
  onPayload: (p: StreamPayload) => void,
): string {
  let next = buffer + chunk
  let nl: number
  while ((nl = next.indexOf('\n')) >= 0) {
    const line = next.slice(0, nl)
    next = next.slice(nl + 1)
    const payload = tryParseDataLine(line)
    if (payload) onPayload(payload)
  }
  return next
}
