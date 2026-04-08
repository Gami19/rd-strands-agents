import type { Dispatch, MutableRefObject, SetStateAction } from 'react'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { formatApiDetail } from '../lib/apiDetail'
import {
  emptyProjectPersist,
  isValidProjectId,
  LS_KEY,
  readBootState,
} from '../lib/persistence'
import type { TeamContextId } from '../lib/teamContext'
import {
  hasAcknowledgedTeamPrNotice,
  setAcknowledgedTeamPrNotice,
  workflowEnabled,
} from '../lib/teamContext'
import type { ChatMessage, ChatMode } from '../types/chat'
import type {
  ProjectListEntry,
  ProjectPersist,
  UploadedRef,
  WorkspaceQuoteRef,
} from '../types/project'

const TEAM_IDS: TeamContextId[] = [
  'developer',
  'marketing',
  'hr',
  'pmo',
  'engineering',
]

function toTeamContextId(raw: string | undefined): TeamContextId {
  if (raw && (TEAM_IDS as readonly string[]).includes(raw)) {
    return raw as TeamContextId
  }
  return 'developer'
}

function teamContextForSwitch(entry: ProjectListEntry | undefined): string {
  if (!entry || entry.meta_error) return 'developer'
  return entry.team_context ?? 'developer'
}

export type UseProjectVaultParams = {
  showToast: (message: string) => void
  setError: Dispatch<SetStateAction<string | null>>
  clearApprovalAndError: () => void
  isProjectDeleteBlockedRef: MutableRefObject<boolean>
}

export function useProjectVault({
  showToast,
  setError,
  clearApprovalAndError,
  isProjectDeleteBlockedRef,
}: UseProjectVaultParams) {
  const boot = useMemo(() => readBootState(), [])
  const vaultRef = useRef<Record<string, ProjectPersist>>({ ...boot.vault })
  const pendingAfterTeamPrAckRef = useRef<(() => void) | null>(null)

  const [activeProjectId, setActiveProjectId] = useState(boot.activeProjectId)
  const [projectList, setProjectList] = useState<ProjectListEntry[]>([])
  const [projectListError, setProjectListError] = useState<string | null>(null)
  const [projectListLoading, setProjectListLoading] = useState(false)

  const [projectCreateOpen, setProjectCreateOpen] = useState(false)
  const [projectCreateId, setProjectCreateId] = useState('')
  const [projectCreateDisplayName, setProjectCreateDisplayName] = useState('')
  const [projectCreateTeamContext, setProjectCreateTeamContext] =
    useState<TeamContextId>('developer')
  const [projectCreateBusy, setProjectCreateBusy] = useState(false)
  const [projectCreateError, setProjectCreateError] = useState<string | null>(
    null,
  )

  const [projectSettingsOpen, setProjectSettingsOpen] = useState(false)
  const [projectSettingsDisplayName, setProjectSettingsDisplayName] =
    useState('')
  const [projectSettingsTeamContext, setProjectSettingsTeamContext] =
    useState<TeamContextId>('developer')
  const [projectSettingsBusy, setProjectSettingsBusy] = useState(false)
  const [projectSettingsError, setProjectSettingsError] = useState<
    string | null
  >(null)

  const [teamPrNoticeOpen, setTeamPrNoticeOpen] = useState(false)

  const [messages, setMessages] = useState<ChatMessage[]>(boot.slice.messages)
  const [input, setInput] = useState(boot.slice.input)
  const [mode, setMode] = useState<ChatMode>(boot.slice.mode)
  const [agentId, setAgentId] = useState<string>(boot.slice.agentId)
  const [uploadedRefs, setUploadedRefs] = useState<UploadedRef[]>(
    boot.slice.uploadedRefs,
  )
  const [workspaceQuotes, setWorkspaceQuotes] = useState<WorkspaceQuoteRef[]>(
    boot.slice.workspaceQuotes,
  )
  const [teamLandingOpen, setTeamLandingOpen] = useState<boolean>(
    boot.slice.teamLandingOpen,
  )

  const fetchProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const res = await fetch('/api/projects')
      const data = (await res.json().catch(() => ({}))) as {
        items?: {
          project_id: string
          display_name?: string
          team_context?: string
          team_context_label?: string
          meta_error?: boolean
          detail?: string
        }[]
        detail?: unknown
      }
      if (!res.ok) {
        setProjectListError(
          formatApiDetail(data.detail, `プロジェクト一覧を取得できません（HTTP ${res.status}）`),
        )
        return
      }
      const items: ProjectListEntry[] = []
      for (const x of Array.isArray(data.items) ? data.items : []) {
        const id = x.project_id
        if (typeof id !== 'string' || !isValidProjectId(id)) continue
        const dnRaw = x.display_name
        const dn =
          typeof dnRaw === 'string' && dnRaw.trim() ? dnRaw.trim() : id
        items.push({
          project_id: id,
          display_name: dn,
          team_context:
            typeof x.team_context === 'string' ? x.team_context : undefined,
          team_context_label:
            typeof x.team_context_label === 'string'
              ? x.team_context_label
              : undefined,
          meta_error: x.meta_error === true,
          detail: typeof x.detail === 'string' ? x.detail : undefined,
        })
      }
      items.sort((a, b) =>
        a.display_name.localeCompare(b.display_name, 'ja', {
          sensitivity: 'base',
        }),
      )
      setProjectList(items)
      setProjectListError(null)
    } catch (e) {
      setProjectListError(
        e instanceof Error
          ? e.message
          : 'プロジェクト一覧の取得に失敗しました（ネットワークまたは /api を確認）',
      )
    } finally {
      setProjectListLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchProjectList()
  }, [fetchProjectList])

  const applySwitchProject = useCallback(
    (nextId: string) => {
      if (nextId === activeProjectId) return
      vaultRef.current = {
        ...vaultRef.current,
        [activeProjectId]: {
          messages,
          workspaceQuotes,
          agentId,
          mode,
          input,
          uploadedRefs,
          teamLandingOpen,
        },
      }
      const slice = vaultRef.current[nextId] ?? emptyProjectPersist()
      const entry = projectList.find((p) => p.project_id === nextId)
      const tc = teamContextForSwitch(entry)
      let nextMode = slice.mode
      if (nextMode === 'workflow' && !workflowEnabled(tc)) {
        nextMode = 'skills'
      }
      setMessages(slice.messages)
      setWorkspaceQuotes(slice.workspaceQuotes)
      setAgentId(slice.agentId)
      setMode(nextMode)
      setInput(slice.input)
      setUploadedRefs(slice.uploadedRefs)
      const forcedLanding = tc !== 'developer'
      setTeamLandingOpen(forcedLanding ? true : slice.teamLandingOpen)
      setActiveProjectId(nextId)
      clearApprovalAndError()
    },
    [
      activeProjectId,
      messages,
      workspaceQuotes,
      agentId,
      mode,
      input,
      uploadedRefs,
      teamLandingOpen,
      projectList,
      clearApprovalAndError,
    ],
  )

  const persistToStorage = useCallback(() => {
    vaultRef.current = {
      ...vaultRef.current,
      [activeProjectId]: {
        messages,
        workspaceQuotes,
        agentId,
        mode,
        input,
        uploadedRefs,
        teamLandingOpen,
      },
    }
    try {
      localStorage.setItem(
        LS_KEY,
        JSON.stringify({
          activeProjectId,
          byProject: vaultRef.current,
        }),
      )
    } catch (e) {
      console.warn('localStorage に保存できませんでした', e)
    }
  }, [
    activeProjectId,
    messages,
    workspaceQuotes,
    agentId,
    mode,
    input,
    uploadedRefs,
    teamLandingOpen,
  ])

  useEffect(() => {
    persistToStorage()
  }, [persistToStorage])

  const doCreateProject = useCallback(async () => {
    const id = projectCreateId.trim()
    const displayName = projectCreateDisplayName.trim()
    setProjectCreateError(null)
    setProjectCreateBusy(true)
    try {
      const body: {
        project_id: string
        display_name?: string
        team_context: string
      } = {
        project_id: id,
        team_context: projectCreateTeamContext,
      }
      if (displayName) body.display_name = displayName
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = (await res.json().catch(() => ({}))) as {
        detail?: unknown
      }
      if (!res.ok) {
        throw new Error(
          formatApiDetail(data.detail, '作成に失敗しました'),
        )
      }
      vaultRef.current[id] = emptyProjectPersist()
      await fetchProjectList()
      applySwitchProject(id)
      setProjectCreateOpen(false)
      setProjectCreateId('')
      setProjectCreateDisplayName('')
      setProjectCreateTeamContext('developer')
      showToast('プロジェクトを作成しました')
    } catch (e) {
      setProjectCreateError(
        e instanceof Error ? e.message : '作成に失敗しました',
      )
    } finally {
      setProjectCreateBusy(false)
    }
  }, [
    projectCreateId,
    projectCreateDisplayName,
    projectCreateTeamContext,
    fetchProjectList,
    applySwitchProject,
    showToast,
  ])

  const submitCreateProject = useCallback(() => {
    const id = projectCreateId.trim()
    const displayName = projectCreateDisplayName.trim()
    setProjectCreateError(null)
    if (!isValidProjectId(id)) {
      setProjectCreateError(
        'プロジェクト ID は 1〜128 文字、英数字・._- のみ使用できます',
      )
      return
    }
    if (displayName.length > 200) {
      setProjectCreateError('表示名は 200 文字以内にしてください')
      return
    }
    const run = () => {
      void doCreateProject()
    }
    if (
      projectCreateTeamContext === 'developer' ||
      hasAcknowledgedTeamPrNotice()
    ) {
      run()
      return
    }
    pendingAfterTeamPrAckRef.current = run
    setTeamPrNoticeOpen(true)
  }, [
    projectCreateId,
    projectCreateDisplayName,
    projectCreateTeamContext,
    doCreateProject,
  ])

  const doSaveProjectSettings = useCallback(async () => {
    const dn = projectSettingsDisplayName.trim()
    setProjectSettingsError(null)
    if (dn.length > 200) {
      setProjectSettingsError('表示名は 200 文字以内にしてください')
      return
    }
    setProjectSettingsBusy(true)
    try {
      const res = await fetch(
        `/api/projects/${encodeURIComponent(activeProjectId)}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            display_name: dn || undefined,
            team_context: projectSettingsTeamContext,
          }),
        },
      )
      const data = (await res.json().catch(() => ({}))) as { detail?: unknown }
      if (!res.ok) {
        throw new Error(
          formatApiDetail(data.detail, '保存に失敗しました'),
        )
      }
      await fetchProjectList()
      setProjectSettingsOpen(false)
      showToast('プロジェクト設定を保存しました')
    } catch (e) {
      setProjectSettingsError(
        e instanceof Error ? e.message : '保存に失敗しました',
      )
    } finally {
      setProjectSettingsBusy(false)
    }
  }, [
    activeProjectId,
    projectSettingsDisplayName,
    projectSettingsTeamContext,
    fetchProjectList,
    showToast,
  ])

  const submitProjectSettings = useCallback(() => {
    const run = () => {
      void doSaveProjectSettings()
    }
    if (
      projectSettingsTeamContext === 'developer' ||
      hasAcknowledgedTeamPrNotice()
    ) {
      run()
      return
    }
    pendingAfterTeamPrAckRef.current = run
    setTeamPrNoticeOpen(true)
  }, [projectSettingsTeamContext, doSaveProjectSettings])

  const openProjectSettings = useCallback(() => {
    const e = projectList.find((p) => p.project_id === activeProjectId)
    setProjectSettingsDisplayName(e?.display_name ?? activeProjectId)
    setProjectSettingsTeamContext(toTeamContextId(e?.team_context))
    setProjectSettingsError(null)
    setProjectSettingsOpen(true)
  }, [activeProjectId, projectList])

  const closeProjectSettings = useCallback(() => {
    if (projectSettingsBusy) return
    setProjectSettingsOpen(false)
    setProjectSettingsError(null)
  }, [projectSettingsBusy])

  const confirmTeamPrNotice = useCallback(() => {
    setAcknowledgedTeamPrNotice()
    setTeamPrNoticeOpen(false)
    const fn = pendingAfterTeamPrAckRef.current
    pendingAfterTeamPrAckRef.current = null
    fn?.()
  }, [])

  const closeTeamPrNotice = useCallback(() => {
    setTeamPrNoticeOpen(false)
    pendingAfterTeamPrAckRef.current = null
  }, [])

  const deleteActiveProject = useCallback(async () => {
    if (activeProjectId === 'default') return
    const dn =
      projectList.find((p) => p.project_id === activeProjectId)?.display_name ??
      activeProjectId
    if (
      !window.confirm(
        `プロジェクト「${dn}」（ID: ${activeProjectId}）のフォルダを削除します。よろしいですか？`,
      )
    )
      return
    if (isProjectDeleteBlockedRef.current) return
    setError(null)
    try {
      const res = await fetch(
        `/api/projects/${encodeURIComponent(activeProjectId)}`,
        { method: 'DELETE' },
      )
      const data = (await res.json().catch(() => ({}))) as {
        detail?: unknown
      }
      if (!res.ok) {
        throw new Error(
          formatApiDetail(data.detail, '削除に失敗しました'),
        )
      }
      const pid = activeProjectId
      const nextVault = { ...vaultRef.current }
      delete nextVault[pid]
      vaultRef.current = nextVault
      const nextSlice = vaultRef.current['default'] ?? emptyProjectPersist()
      setMessages(nextSlice.messages)
      setWorkspaceQuotes(nextSlice.workspaceQuotes)
      setAgentId(nextSlice.agentId)
      setMode(nextSlice.mode)
      setInput(nextSlice.input)
      setUploadedRefs(nextSlice.uploadedRefs)
      setTeamLandingOpen(false)
      setActiveProjectId('default')
      clearApprovalAndError()
      try {
        localStorage.setItem(
          LS_KEY,
          JSON.stringify({
            activeProjectId: 'default',
            byProject: vaultRef.current,
          }),
        )
      } catch (e) {
        console.warn(e)
      }
      await fetchProjectList()
      showToast('プロジェクトを削除しました')
    } catch (e) {
      setError(e instanceof Error ? e.message : '削除に失敗しました')
    }
  }, [
    activeProjectId,
    isProjectDeleteBlockedRef,
    fetchProjectList,
    showToast,
    projectList,
    setError,
    clearApprovalAndError,
  ])

  const displayNameForProjectId = useCallback(
    (id: string) =>
      projectList.find((p) => p.project_id === id)?.display_name ?? id,
    [projectList],
  )

  const labelForProjectOption = useCallback(
    (id: string) => {
      const p = projectList.find((x) => x.project_id === id)
      if (!p) return displayNameForProjectId(id)
      if (p.meta_error) return `${p.display_name}（メタデータエラー）`
      return p.display_name
    },
    [projectList, displayNameForProjectId],
  )

  const activeProjectListEntry = useMemo(
    () => projectList.find((p) => p.project_id === activeProjectId),
    [projectList, activeProjectId],
  )

  const projectOptions = useMemo(() => {
    const ids = new Set(projectList.map((p) => p.project_id))
    ids.add(activeProjectId)
    ids.add('default')
    return [...ids].sort((a, b) => a.localeCompare(b))
  }, [projectList, activeProjectId])

  return {
    activeProjectId,
    activeProjectListEntry,
    projectList,
    projectListError,
    projectListLoading,
    fetchProjectList,
    projectCreateOpen,
    setProjectCreateOpen,
    projectCreateId,
    setProjectCreateId,
    projectCreateDisplayName,
    setProjectCreateDisplayName,
    projectCreateTeamContext,
    setProjectCreateTeamContext,
    projectCreateBusy,
    projectCreateError,
    setProjectCreateError,
    projectSettingsOpen,
    projectSettingsDisplayName,
    setProjectSettingsDisplayName,
    projectSettingsTeamContext,
    setProjectSettingsTeamContext,
    projectSettingsBusy,
    projectSettingsError,
    openProjectSettings,
    closeProjectSettings,
    submitProjectSettings,
    teamPrNoticeOpen,
    confirmTeamPrNotice,
    closeTeamPrNotice,
    messages,
    setMessages,
    input,
    setInput,
    mode,
    setMode,
    agentId,
    setAgentId,
    uploadedRefs,
    setUploadedRefs,
    workspaceQuotes,
    setWorkspaceQuotes,
    teamLandingOpen,
    setTeamLandingOpen,
    applySwitchProject,
    submitCreateProject,
    deleteActiveProject,
    displayNameForProjectId,
    labelForProjectOption,
    projectOptions,
  }
}
