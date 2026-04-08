import { useCallback, useEffect, useRef } from 'react'

export function useChatComposerLayout(input: string) {
  const listRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const composerTextareaRef = useRef<HTMLTextAreaElement | null>(null)

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      listRef.current?.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: 'smooth',
      })
    })
  }, [])

  const autoResizeComposer = useCallback(() => {
    const el = composerTextareaRef.current
    if (!el) return

    const style = window.getComputedStyle(el)
    const lineHeight = Number.parseFloat(style.lineHeight || '0')
    const paddingTop = Number.parseFloat(style.paddingTop || '0')
    const paddingBottom = Number.parseFloat(style.paddingBottom || '0')

    const maxLines = 7
    const maxHeight =
      (Number.isFinite(lineHeight) && lineHeight > 0 ? lineHeight : 20) *
        maxLines +
      paddingTop +
      paddingBottom

    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`
  }, [])

  useEffect(() => {
    autoResizeComposer()
  }, [input, autoResizeComposer])

  return {
    listRef,
    fileInputRef,
    composerTextareaRef,
    scrollToBottom,
    autoResizeComposer,
  }
}
