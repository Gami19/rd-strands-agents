import type { Dispatch, RefObject, SetStateAction } from 'react'
import { useCallback, useEffect, useRef, useState } from 'react'

export type UseWorkspaceFolderHelpResult = {
  wrapRef: RefObject<HTMLDivElement | null>
  open: boolean
  setOpen: Dispatch<SetStateAction<boolean>>
  openHelp: () => void
  scheduleClose: () => void
  clearCloseTimer: () => void
}

export function useWorkspaceFolderHelp(): UseWorkspaceFolderHelpResult {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement | null>(null)
  const timerRef = useRef<number | null>(null)

  const clearCloseTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const openHelp = useCallback(() => {
    clearCloseTimer()
    setOpen(true)
  }, [clearCloseTimer])

  const scheduleClose = useCallback(() => {
    clearCloseTimer()
    timerRef.current = window.setTimeout(() => {
      setOpen(false)
      timerRef.current = null
    }, 200)
  }, [clearCloseTimer])

  useEffect(() => {
    return () => {
      clearCloseTimer()
    }
  }, [clearCloseTimer])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearCloseTimer()
        setOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, clearCloseTimer])

  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: PointerEvent) => {
      const el = wrapRef.current
      if (el && !el.contains(e.target as Node)) {
        clearCloseTimer()
        setOpen(false)
      }
    }
    document.addEventListener('pointerdown', onPointerDown, true)
    return () => document.removeEventListener('pointerdown', onPointerDown, true)
  }, [open, clearCloseTimer])

  return {
    wrapRef,
    open,
    setOpen,
    openHelp,
    scheduleClose,
    clearCloseTimer,
  }
}
