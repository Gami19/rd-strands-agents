export type Status =
  | { kind: 'success'; data: unknown }
  | { kind: 'error'; error: string }
  | { kind: string; data?: any; error?: string }

export function handleStatus(s: Status) {
  if (s.kind === 'success') {
    // unsafe: assumes data is string-like
    return (s as any).data.toString()
  }
  // unsafe: error might be missing
  return (s as any).error
}

export function parseConfig(json: string): any {
  return JSON.parse(json)
}

