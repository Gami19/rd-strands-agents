import { useCallback } from 'react'

export type CopyTextOptions = {
  skipSuccessToast?: boolean
}

export function useCopyText(showToast: (message: string) => void) {
  const copyText = useCallback(
    async (text: string, options?: CopyTextOptions): Promise<boolean> => {
      try {
        await navigator.clipboard.writeText(text)
        if (!options?.skipSuccessToast) {
          showToast('コピーしました')
        }
        return true
      } catch {
        showToast('コピーに失敗しました')
        return false
      }
    },
    [showToast],
  )

  return { copyText }
}
