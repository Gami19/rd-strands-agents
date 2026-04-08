import type { TeamContextId } from '../lib/teamContext'
import { TEAM_CONTEXT_OPTIONS } from '../lib/teamContext'

export type ProjectSettingsModalProps = {
  open: boolean
  busy: boolean
  projectId: string
  displayName: string
  teamContext: TeamContextId
  error: string | null
  onClose: () => void
  onChangeDisplayName: (v: string) => void
  onChangeTeamContext: (v: TeamContextId) => void
  onSubmit: () => void
}

export function ProjectSettingsModal({
  open,
  busy,
  projectId,
  displayName,
  teamContext,
  error,
  onClose,
  onChangeDisplayName,
  onChangeTeamContext,
  onSubmit,
}: ProjectSettingsModalProps) {
  if (!open) return null
  const teamHintId = 'project-settings-team-hint'
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={() => !busy && onClose()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-settings-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="project-settings-title" className="modal-title">
            プロジェクト設定
          </h2>
          <button
            type="button"
            className="modal-close"
            disabled={busy}
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <p className="modal-hint">
          プロジェクト ID: <code>{projectId}</code>（変更不可）
        </p>
        <label
          className="sidebar-project-field-label"
          htmlFor="project-settings-display"
        >
          表示名
        </label>
        <input
          id="project-settings-display"
          type="text"
          className="sidebar-project-create-input"
          value={displayName}
          disabled={busy}
          autoComplete="off"
          onChange={(e) => onChangeDisplayName(e.target.value)}
        />
        <label
          className="sidebar-project-field-label"
          htmlFor="project-settings-team"
        >
          チーム文脈
        </label>
        <p id={teamHintId} className="modal-hint">
          読み込む Skills のルートと、Workflow
          が使えるか（Developer のみ可）が変わります。
        </p>
        <select
          id="project-settings-team"
          className="sidebar-project-create-input"
          disabled={busy}
          value={teamContext}
          aria-describedby={teamHintId}
          aria-label="チーム文脈（Skills ルートと Workflow 可否）"
          onChange={(e) => onChangeTeamContext(e.target.value as TeamContextId)}
        >
          {TEAM_CONTEXT_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        {error ? (
          <p className="sidebar-project-create-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="composer project-create-actions">
          <button
            type="button"
            className="composer-send"
            disabled={busy}
            onClick={() => void onSubmit()}
          >
            {busy ? '保存中…' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}
