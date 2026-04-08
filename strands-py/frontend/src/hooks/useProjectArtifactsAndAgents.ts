import type { Dispatch, SetStateAction } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { ARTIFACT_FOLDERS, artifactFilePathUrl } from '../lib/artifacts'
import type { ChatMode } from '../types/chat'
import type { AgentListItem, ArtifactItem, UploadedRef } from '../types/project'

export type UseProjectArtifactsAndAgentsParams = {
  activeProjectId: string
  mode: ChatMode
  agentId: string
  setAgentId: Dispatch<SetStateAction<string>>
  setUploadedRefs: Dispatch<SetStateAction<UploadedRef[]>>
  setError: Dispatch<SetStateAction<string | null>>
}

export function useProjectArtifactsAndAgents({
  activeProjectId,
  mode,
  agentId,
  setAgentId,
  setUploadedRefs,
  setError,
}: UseProjectArtifactsAndAgentsParams) {
  const [agents, setAgents] = useState<AgentListItem[]>([])
  const [agentsLoading, setAgentsLoading] = useState(false)
  const [agentsError, setAgentsError] = useState<string | null>(null)
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([])
  const [artifactsLoading, setArtifactsLoading] = useState(false)
  const [artifactDeletingKey, setArtifactDeletingKey] = useState<string | null>(
    null,
  )

  const loadArtifacts = useCallback(async () => {
    setArtifactsLoading(true)
    try {
      const res = await fetch(
        `/api/projects/${encodeURIComponent(activeProjectId)}/artifacts`,
      )
      if (!res.ok) return
      const data = (await res.json()) as { items?: ArtifactItem[] }
      setArtifacts(Array.isArray(data.items) ? data.items : [])
    } catch {
      setArtifacts([])
    } finally {
      setArtifactsLoading(false)
    }
  }, [activeProjectId])

  const loadAgents = useCallback(async () => {
    setAgentsLoading(true)
    setAgentsError(null)
    try {
      const res = await fetch(
        `/api/agents?project_id=${encodeURIComponent(activeProjectId)}`,
      )
      if (!res.ok) {
        setAgents([])
        setAgentsError(`一覧を取得できません（HTTP ${res.status}）`)
        return
      }
      const data = (await res.json()) as { items?: AgentListItem[] }
      const raw = Array.isArray(data.items) ? data.items : []
      const items = raw.filter((a) => (a.kind ?? 'single') !== 'orchestrator')
      setAgents(items)
      setAgentId((prev) => (items.some((a) => a.agent_id === prev) ? prev : ''))
    } catch {
      setAgents([])
      setAgentsError('一覧の取得に失敗しました（バックエンド起動と /api を確認）')
    } finally {
      setAgentsLoading(false)
    }
  }, [activeProjectId, setAgentId])

  useEffect(() => {
    void loadArtifacts()
  }, [loadArtifacts])

  useEffect(() => {
    void loadAgents()
  }, [loadAgents])

  useEffect(() => {
    if (mode !== 'skills') return
    void loadAgents()
  }, [mode, loadAgents])

  useEffect(() => {
    if (mode !== 'workflow') return
    if (agentId) return
    setAgentId('convert-pdf')
  }, [mode, agentId, setAgentId])

  const deleteArtifact = useCallback(
    async (folder: string, filename: string) => {
      const key = `${folder}/${filename}`
      if (!window.confirm(`「${folder}/${filename}」を削除しますか？`)) return
      setArtifactDeletingKey(key)
      setError(null)
      try {
        const res = await fetch(
          artifactFilePathUrl(activeProjectId, folder, filename),
          {
            method: 'DELETE',
          },
        )
        if (!res.ok) {
          const data = (await res.json().catch(() => ({}))) as {
            detail?: string | { msg?: string }[]
          }
          const d = data.detail
          const msg =
            typeof d === 'string'
              ? d
              : Array.isArray(d)
                ? d.map((x) => ('msg' in x ? String(x.msg) : JSON.stringify(x))).join('; ')
                : res.statusText
          throw new Error(msg || '削除に失敗しました')
        }
        const expectedBase = artifactFilePathUrl(activeProjectId, folder, filename)
        setUploadedRefs((prev) =>
          prev.filter((r) => r.url.split('?')[0] !== expectedBase),
        )
        void loadArtifacts()
      } catch (e) {
        setError(e instanceof Error ? e.message : '削除エラー')
      } finally {
        setArtifactDeletingKey(null)
      }
    },
    [loadArtifacts, activeProjectId, setError, setUploadedRefs],
  )

  const artifactsByFolder = useMemo(
    () =>
      ARTIFACT_FOLDERS.map((folder) => ({
        folder,
        items: artifacts.filter((a) => a.folder.replace(/\/+$/, '') === folder),
      })).filter((group) => group.items.length > 0),
    [artifacts],
  )

  return {
    agents,
    agentsLoading,
    agentsError,
    artifacts,
    artifactsLoading,
    artifactDeletingKey,
    loadArtifacts,
    loadAgents,
    deleteArtifact,
    artifactsByFolder,
  }
}
