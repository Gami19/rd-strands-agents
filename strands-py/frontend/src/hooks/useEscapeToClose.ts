import { useEffect } from 'react'

export type UseEscapeToCloseParams = {
  open: boolean
  onClose: () => void
  enabled?: boolean
}

export function useEscapeToClose({
  open,
  onClose,
  enabled = true,
}: UseEscapeToCloseParams): void {
  useEffect(() => {
    if (!open || !enabled) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, enabled, onClose])
}
