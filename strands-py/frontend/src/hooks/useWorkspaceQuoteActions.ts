import type { RefObject } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { useCallback } from 'react'
import type { WorkspaceQuoteRef } from '../types/project'

export function useWorkspaceQuoteActions(
  setWorkspaceQuotes: Dispatch<SetStateAction<WorkspaceQuoteRef[]>>,
  composerTextareaRef: RefObject<HTMLTextAreaElement | null>,
) {
  const insertWorkspaceTarget = useCallback(
    (folder: string, filename: string) => {
      setWorkspaceQuotes((prev) => {
        const key = `${folder}/${filename}`
        if (prev.some((q) => `${q.area}/${q.filename}` === key)) return prev
        return [
          ...prev,
          { id: crypto.randomUUID(), area: folder, filename },
        ]
      })
      requestAnimationFrame(() => composerTextareaRef.current?.focus())
    },
    [setWorkspaceQuotes, composerTextareaRef],
  )

  const removeWorkspaceQuote = useCallback(
    (id: string) => {
      setWorkspaceQuotes((prev) => prev.filter((q) => q.id !== id))
    },
    [setWorkspaceQuotes],
  )

  return { insertWorkspaceTarget, removeWorkspaceQuote }
}
