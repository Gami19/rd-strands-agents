import type { TeamContextId } from '../lib/teamContext'
import { TEAM_CONTEXT_OPTIONS } from '../lib/teamContext'

export type ProjectCreateModalProps = {
  open: boolean
  projectCreateBusy: boolean
  projectCreateId: string
  projectCreateDisplayName: string
  projectCreateTeamContext: TeamContextId
  projectCreateError: string | null
  onClose: () => void
  onChangeId: (v: string) => void
  onChangeDisplayName: (v: string) => void
  onChangeTeamContext: (v: TeamContextId) => void
  onSubmit: () => void
}

export function ProjectCreateModal({
  open,
  projectCreateBusy,
  projectCreateId,
  projectCreateDisplayName,
  projectCreateTeamContext,
  projectCreateError,
  onClose,
  onChangeId,
  onChangeDisplayName,
  onChangeTeamContext,
  onSubmit,
}: ProjectCreateModalProps) {
  if (!open) return null
  const teamHintId = 'project-create-team-hint'
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={() => !projectCreateBusy && onClose()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-create-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="project-create-title" className="modal-title">
            プロジェクトを作成
          </h2>
          <button
            type="button"
            className="modal-close"
            disabled={projectCreateBusy}
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <p className="modal-hint">
          プロジェクト ID はフォルダ名・API 用です（英数字・._- のみ、1〜128
          文字）。表示名は日本語を含めてよく、省略すると ID と同じになります。
        </p>
        <label className="sidebar-project-field-label" htmlFor="project-create-id">
          プロジェクト ID
        </label>
        <input
          id="project-create-id"
          type="text"
          className="sidebar-project-create-input"
          value={projectCreateId}
          disabled={projectCreateBusy}
          placeholder="例: my-project"
          autoComplete="off"
          onChange={(e) => onChangeId(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !projectCreateBusy) {
              e.preventDefault()
              void onSubmit()
            }
          }}
        />
        <label
          className="sidebar-project-field-label"
          htmlFor="project-create-display"
        >
          表示名（任意・日本語可）
        </label>
        <input
          id="project-create-display"
          type="text"
          className="sidebar-project-create-input"
          value={projectCreateDisplayName}
          disabled={projectCreateBusy}
          placeholder="例: 営業デモ用（空欄なら ID と同じ）"
          autoComplete="off"
          onChange={(e) => onChangeDisplayName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !projectCreateBusy) {
              e.preventDefault()
              void onSubmit()
            }
          }}
        />
        <label
          className="sidebar-project-field-label"
          htmlFor="project-create-team"
        >
          チーム文脈
        </label>
        <p id={teamHintId} className="modal-hint">
          読み込む Skills のルートと、Workflow
          が使えるか（Developer のみ可）が変わります。
        </p>
        <select
          id="project-create-team"
          className="sidebar-project-create-input"
          disabled={projectCreateBusy}
          value={projectCreateTeamContext}
          aria-describedby={teamHintId}
          aria-label="チーム文脈（Skills ルートと Workflow 可否）"
          onChange={(e) =>
            onChangeTeamContext(e.target.value as TeamContextId)
          }
        >
          {TEAM_CONTEXT_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        {projectCreateError ? (
          <p className="sidebar-project-create-error" role="alert">
            {projectCreateError}
          </p>
        ) : null}
        <div className="composer project-create-actions">
          <button
            type="button"
            className="composer-send"
            disabled={projectCreateBusy}
            onClick={() => void onSubmit()}
          >
            {projectCreateBusy ? '作成中…' : '作成'}
          </button>
        </div>
      </div>
    </div>
  )
}
