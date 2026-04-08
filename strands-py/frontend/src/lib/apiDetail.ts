export function formatApiDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) =>
        typeof d === 'object' && d !== null
          ? ('msg' in d && typeof (d as { msg?: string }).msg === 'string'
              ? (d as { msg: string }).msg
              : null) ??
            ('message' in d &&
            typeof (d as { message?: string }).message === 'string'
              ? (d as { message: string }).message
              : null) ??
            JSON.stringify(d)
          : String(d),
      )
      .join('; ')
  }
  if (detail && typeof detail === 'object') {
    const o = detail as { msg?: string; message?: string }
    if (typeof o.message === 'string' && o.message) return o.message
    if (typeof o.msg === 'string' && o.msg) return o.msg
  }
  return fallback
}
