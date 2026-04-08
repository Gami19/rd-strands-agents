import { useCallback, useEffect, useRef, useState } from 'react'

export function useToast(durationMs = 1500): {
  toast: string | null
  showToast: (message: string) => void
} {
  const [toast, setToast] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [])

  const showToast = useCallback(
    (message: string) => {
      setToast(message)
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
      }
      timerRef.current = window.setTimeout(() => {
        setToast(null)
        timerRef.current = null
      }, durationMs)
    },
    [durationMs],
  )

  return { toast, showToast }
}
