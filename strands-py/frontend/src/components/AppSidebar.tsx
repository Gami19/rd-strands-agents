import { useEffect, useState } from 'react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import { agentYamlDisplayName } from '../lib/agentsDisplay'
import { formatBytes } from '../lib/formatBytes'
import { agentIdFromAgentsFilename } from '../lib/workspace'
import { WORKSPACE_FOLDER_HELP } from '../lib/workspace'
import type { AgentListItem, ArtifactItem } from '../types/project'

export type ArtifactGroup = { folder: string; items: ArtifactItem[] }

function groupAgentsArtifactsByDivision(
  items: ArtifactItem[],
  agents: AgentListItem[],
): { label: string; items: ArtifactItem[] }[] {
  const map = new Map<string, ArtifactItem[]>()
  for (const it of items) {
    const aid = agentIdFromAgentsFilename(it.filename)
    const meta = agents.find((a) => a.agent_id === aid)
    const label =
      typeof meta?.division === 'string' && meta.division.trim()
        ? meta.division.trim()
        : 'メンバー'
    const list = map.get(label) ?? []
    list.push(it)
    map.set(label, list)
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b, 'ja'))
    .map(([label, grouped]) => ({
      label,
      items: grouped.sort((x, y) => x.filename.localeCompare(y.filename, 'ja')),
    }))
}

export type AppSidebarProps = {
  activeProjectId: string
  projectOptions: string[]
  labelForProjectOption: (id: string) => string
  activeProjectTeamContextLabel: string | null
  activeProjectMetaError: boolean
  activeProjectMetaDetail: string | null
  projectListError: string | null
  projectListLoading: boolean
  onRetryProjectList: () => void
  projectSelectDisabled: boolean
  onSwitchProject: (id: string) => void
  onOpenCreateProject: () => void
  onOpenProjectSettings: () => void
  onDeleteProject: () => void
  projectCreateBusy: boolean
  projectSettingsBusy: boolean
  onNewChat: () => void
  workspaceFolderHelpWrapRef: RefObject<HTMLDivElement | null>
  workspaceFolderHelpOpen: boolean
  openWorkspaceFolderHelp: () => void
  scheduleCloseWorkspaceFolderHelp: () => void
  clearWorkspaceFolderHelpTimer: () => void
  setWorkspaceFolderHelpOpen: Dispatch<SetStateAction<boolean>>
  onRefreshArtifacts: () => void
  artifactsLoading: boolean
  artifacts: ArtifactItem[]
  artifactsByFolder: ArtifactGroup[]
  agents: AgentListItem[]
  artifactDeletingKey: string | null
  onInsertWorkspaceTarget: (folder: string, filename: string) => void
  onDeleteArtifact: (folder: string, filename: string) => void
}

export function AppSidebar({
  activeProjectId,
  projectOptions,
  labelForProjectOption,
  activeProjectTeamContextLabel,
  activeProjectMetaError,
  activeProjectMetaDetail,
  projectListError,
  projectListLoading,
  onRetryProjectList,
  projectSelectDisabled,
  onSwitchProject,
  onOpenCreateProject,
  onOpenProjectSettings,
  onDeleteProject,
  projectCreateBusy,
  projectSettingsBusy,
  onNewChat,
  workspaceFolderHelpWrapRef,
  workspaceFolderHelpOpen,
  openWorkspaceFolderHelp,
  scheduleCloseWorkspaceFolderHelp,
  clearWorkspaceFolderHelpTimer,
  setWorkspaceFolderHelpOpen,
  onRefreshArtifacts,
  artifactsLoading,
  artifacts,
  artifactsByFolder,
  agents,
  artifactDeletingKey,
  onInsertWorkspaceTarget,
  onDeleteArtifact,
}: AppSidebarProps) {
  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({})

  useEffect(() => {
    setCollapsedFolders((prev) => {
      const next = { ...prev }
      for (const group of artifactsByFolder) {
        if (next[group.folder] === undefined) {
          next[group.folder] = false
        }
      }
      return next
    })
  }, [artifactsByFolder])

  const toggleFolder = (folder: string) => {
    setCollapsedFolders((prev) => ({ ...prev, [folder]: !prev[folder] }))
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-upper">
        <div className="sidebar-brand">Strands Skills</div>
        <div className="sidebar-meta sidebar-meta-project">
          <span className="sidebar-meta-label">project</span>
          <div className="sidebar-project-controls">
            <span id="project-context-desc" className="sr-only">
              {activeProjectMetaError
                ? 'このプロジェクトのメタデータは読み取れません。'
                : activeProjectTeamContextLabel
                  ? `現在のチーム文脈は ${activeProjectTeamContextLabel} です。`
                  : 'チーム文脈は一覧取得後に表示されます。'}
            </span>
            <select
              className="sidebar-project-select"
              aria-label="プロジェクトを選択"
              aria-describedby="project-context-desc"
              value={activeProjectId}
              disabled={projectSelectDisabled}
              title={
                projectSelectDisabled
                  ? 'ストリーミングまたはツール承認中は切り替えできません'
                  : 'プロジェクトを切り替え'
              }
              onChange={(e) => onSwitchProject(e.target.value)}
            >
              {projectOptions.map((id) => (
                <option key={id} value={id} title={`ID: ${id}`}>
                  {labelForProjectOption(id)}
                </option>
              ))}
            </select>
            <div className="sidebar-project-active-id" aria-hidden>
              ID: {activeProjectId}
            </div>
            {activeProjectMetaError && activeProjectMetaDetail ? (
              <p className="sidebar-project-meta-error" role="alert">
                メタデータエラー: {activeProjectMetaDetail}
              </p>
            ) : null}
            {projectListError ? (
              <div className="sidebar-project-list-error" role="alert">
                <p>{projectListError}</p>
                <button
                  type="button"
                  className="sidebar-project-btn"
                  disabled={projectListLoading}
                  onClick={() => void onRetryProjectList()}
                >
                  {projectListLoading ? '再試行中…' : '再試行'}
                </button>
              </div>
            ) : null}
            <div className="sidebar-project-actions">
              <button
                type="button"
                className="sidebar-project-btn"
                disabled={projectSelectDisabled || projectCreateBusy}
                onClick={onOpenCreateProject}
              >
                新規
              </button>
              <button
                type="button"
                className="sidebar-project-btn"
                disabled={
                  projectSelectDisabled ||
                  projectCreateBusy ||
                  projectSettingsBusy
                }
                onClick={onOpenProjectSettings}
              >
                設定
              </button>
              <button
                type="button"
                className="sidebar-project-btn sidebar-project-btn-danger"
                disabled={
                  projectSelectDisabled ||
                  activeProjectId === 'default' ||
                  projectCreateBusy
                }
                onClick={onDeleteProject}
              >
                削除
              </button>
            </div>
          </div>
        </div>
        <button type="button" className="sidebar-new" onClick={onNewChat}>
          新しいチャット
        </button>
      </div>
      <div className="sidebar-lower">
        <div className="sidebar-artifacts-head">
          <div className="sidebar-artifacts-head-start">
            <span className="sidebar-artifacts-title">Workspace</span>
            <div
              ref={workspaceFolderHelpWrapRef}
              className="sidebar-workspace-help-wrap"
              onMouseEnter={openWorkspaceFolderHelp}
              onMouseLeave={scheduleCloseWorkspaceFolderHelp}
            >
              <button
                type="button"
                className="sidebar-workspace-help-btn"
                aria-label="各フォルダの役割を表示"
                aria-expanded={workspaceFolderHelpOpen}
                aria-haspopup="dialog"
                aria-controls="workspace-folder-help-dialog"
                title="フォルダの役割"
                onFocus={openWorkspaceFolderHelp}
                onBlur={scheduleCloseWorkspaceFolderHelp}
                onClick={() => {
                  if (!window.matchMedia('(hover: hover)').matches) {
                    clearWorkspaceFolderHelpTimer()
                    setWorkspaceFolderHelpOpen((o) => !o)
                  }
                }}
              >
                ?
              </button>
              {workspaceFolderHelpOpen ? (
                <div
                  id="workspace-folder-help-dialog"
                  className="sidebar-workspace-help-panel"
                  role="dialog"
                  aria-label="Workspace フォルダの説明"
                  onMouseEnter={openWorkspaceFolderHelp}
                  onMouseLeave={scheduleCloseWorkspaceFolderHelp}
                >
                  <div className="sidebar-workspace-help-panel-title">
                    フォルダの役割
                  </div>
                  <ul className="sidebar-workspace-help-list">
                    {WORKSPACE_FOLDER_HELP.map((row) => (
                      <li key={row.folder}>
                        <span className="sidebar-workspace-help-folder">
                          {row.folder}/
                        </span>
                        <span className="sidebar-workspace-help-desc">
                          {row.description}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            className="sidebar-artifacts-refresh"
            onClick={() => void onRefreshArtifacts()}
            disabled={artifactsLoading}
            aria-label="成果物一覧を更新"
            title="更新"
          >
            ↻
          </button>
        </div>
        <div className="sidebar-artifacts-scroll">
          {artifactsLoading && artifacts.length === 0 ? (
            <p className="sidebar-artifacts-muted">読み込み中…</p>
          ) : null}
          {!artifactsLoading && artifacts.length === 0 ? (
            <p className="sidebar-artifacts-muted">まだファイルがありません</p>
          ) : null}
          {artifactsByFolder.map((group) => (
            <section key={group.folder} className="sidebar-artifacts-group">
              <div className="sidebar-artifacts-group-head">
                <h3 className="sidebar-artifacts-group-title">{group.folder}/</h3>
                <button
                  type="button"
                  className="sidebar-artifacts-group-toggle"
                  onClick={() => toggleFolder(group.folder)}
                  aria-label={`${group.folder} フォルダを${
                    collapsedFolders[group.folder] ? '展開' : '折りたたみ'
                  }`}
                  aria-expanded={!collapsedFolders[group.folder]}
                >
                  {collapsedFolders[group.folder] ? '▶' : '▼'}
                </button>
              </div>
              {!collapsedFolders[group.folder] &&
              (group.folder === 'agents' ? (
                <>
                  {groupAgentsArtifactsByDivision(group.items, agents).map((g) => (
                    <section key={g.label} className="sidebar-division-group">
                      <h4 className="sidebar-division-title">{g.label}</h4>
                      <ul className="sidebar-artifacts-list">
                        {g.items.map((a) => {
                          const rowKey = `${a.folder}/${a.filename}`
                          const busy = artifactDeletingKey === rowKey
                          const displayName = agentYamlDisplayName(a.filename, agents)
                          return (
                            <li key={rowKey} className="sidebar-artifact-row">
                              <div className="sidebar-artifact-main">
                                <span className="sidebar-artifact-folder">{a.folder}</span>
                                <a
                                  className="sidebar-artifact-name"
                                  href={`${a.url}?download=1`}
                                  download={a.filename}
                                >
                                  {displayName}
                                </a>
                                <span className="sidebar-artifact-size">
                                  {formatBytes(a.size)}
                                </span>
                              </div>
                              <div className="sidebar-artifact-actions">
                                <button
                                  type="button"
                                  className="sidebar-artifact-insert"
                                  disabled={busy || artifactsLoading}
                                  onClick={() =>
                                    onInsertWorkspaceTarget(a.folder, a.filename)
                                  }
                                  title="参照ブロックとしてコンポーザーに追加"
                                  aria-label={`${displayName} を参照ブロックとして追加`}
                                >
                                  <svg
                                    width="15"
                                    height="15"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    aria-hidden
                                  >
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                    <polyline points="14 2 14 8 20 8" />
                                    <line x1="12" y1="18" x2="12" y2="12" />
                                    <line x1="9" y1="15" x2="15" y2="15" />
                                  </svg>
                                </button>
                                <button
                                  type="button"
                                  className="sidebar-artifact-delete"
                                  disabled={busy || artifactsLoading}
                                  onClick={() => void onDeleteArtifact(a.folder, a.filename)}
                                  aria-label={`${displayName} を削除`}
                                  title="削除"
                                >
                                  {busy ? '…' : '×'}
                                </button>
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    </section>
                  ))}
                </>
              ) : (
                <ul className="sidebar-artifacts-list">
                  {group.items.map((a) => {
                    const rowKey = `${a.folder}/${a.filename}`
                    const busy = artifactDeletingKey === rowKey
                    return (
                      <li key={rowKey} className="sidebar-artifact-row">
                        <div className="sidebar-artifact-main">
                          <span className="sidebar-artifact-folder">{a.folder}</span>
                          <a
                            className="sidebar-artifact-name"
                            href={`${a.url}?download=1`}
                            download={a.filename}
                          >
                            {a.filename}
                          </a>
                          <span className="sidebar-artifact-size">{formatBytes(a.size)}</span>
                        </div>
                        <div className="sidebar-artifact-actions">
                          <button
                            type="button"
                            className="sidebar-artifact-insert"
                            disabled={busy || artifactsLoading}
                            onClick={() => onInsertWorkspaceTarget(a.folder, a.filename)}
                            title="参照ブロックとしてコンポーザーに追加"
                            aria-label={`${a.filename} を参照ブロックとして追加`}
                          >
                            <svg
                              width="15"
                              height="15"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              aria-hidden
                            >
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                              <line x1="12" y1="18" x2="12" y2="12" />
                              <line x1="9" y1="15" x2="15" y2="15" />
                            </svg>
                          </button>
                          <button
                            type="button"
                            className="sidebar-artifact-delete"
                            disabled={busy || artifactsLoading}
                            onClick={() => void onDeleteArtifact(a.folder, a.filename)}
                            aria-label={`${a.filename} を削除`}
                            title="削除"
                          >
                            {busy ? '…' : '×'}
                          </button>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              ))}
            </section>
          ))}
        </div>
      </div>
    </aside>
  )
}
