import type { Dispatch, SetStateAction } from 'react'
import { useCallback, useState } from 'react'
import type { UploadedRef } from '../types/project'

export type UseProjectFileUploadParams = {
  activeProjectId: string
  setError: Dispatch<SetStateAction<string | null>>
  setUploadedRefs: Dispatch<SetStateAction<UploadedRef[]>>
  loadArtifacts: () => Promise<void>
}

export function useProjectFileUpload({
  activeProjectId,
  setError,
  setUploadedRefs,
  loadArtifacts,
}: UseProjectFileUploadParams) {
  const [uploadBusy, setUploadBusy] = useState(false)
  const [attachModalOpen, setAttachModalOpen] = useState(false)

  const uploadFiles = useCallback(
    async (files: FileList | null) => {
      const f = files?.[0]
      if (!f || uploadBusy) return
      const lower = f.name.toLowerCase()
      const ok =
        lower.endsWith('.md') ||
        lower.endsWith('.pdf') ||
        lower.endsWith('.png') ||
        lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg') ||
        lower.endsWith('.ts') ||
        lower.endsWith('.tsx') ||
        lower.endsWith('.js') ||
        lower.endsWith('.py') ||
        lower.endsWith('.ipynb')
      if (!ok) {
        setError(
          '.md / .pdf / .png / .jpeg / .ts / .tsx / .js / .py / .ipynb のみアップロードできます',
        )
        return
      }
      setError(null)
      setUploadBusy(true)
      try {
        const form = new FormData()
        form.append('project_id', activeProjectId)
        form.append('file', f)
        const res = await fetch('/api/upload', {
          method: 'POST',
          body: form,
        })
        const data = (await res.json().catch(() => ({}))) as {
          detail?: string | { msg?: string }[]
          status?: string
          kind?: string
          ref?: { url: string; filename: string }
        }
        if (!res.ok) {
          const d = data.detail
          const msg =
            typeof d === 'string'
              ? d
              : Array.isArray(d)
                ? d
                    .map((x) =>
                      'msg' in x ? String(x.msg) : JSON.stringify(x),
                    )
                    .join('; ')
                : res.statusText
          throw new Error(msg || 'アップロードに失敗しました')
        }
        if (
          data.ref &&
          (data.kind === 'markdown' ||
            data.kind === 'pdf' ||
            data.kind === 'image' ||
            data.kind === 'file')
        ) {
          const kind =
            data.kind === 'pdf'
              ? 'pdf'
              : data.kind === 'image'
                ? 'image'
                : data.kind === 'file'
                  ? 'file'
                  : 'markdown'
          setUploadedRefs((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              kind,
              url: data.ref!.url,
              filename: data.ref!.filename,
            },
          ])
          setAttachModalOpen(false)
          void loadArtifacts()
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'アップロードエラー')
      } finally {
        setUploadBusy(false)
      }
    },
    [
      uploadBusy,
      loadArtifacts,
      activeProjectId,
      setError,
      setUploadedRefs,
    ],
  )

  return {
    uploadBusy,
    attachModalOpen,
    setAttachModalOpen,
    uploadFiles,
  }
}
