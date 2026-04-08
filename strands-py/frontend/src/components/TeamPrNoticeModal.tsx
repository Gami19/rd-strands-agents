export type TeamPrNoticeModalProps = {
  open: boolean
  busy: boolean
  onClose: () => void
  onConfirm: () => void
}

export function TeamPrNoticeModal({
  open,
  busy,
  onClose,
  onConfirm,
}: TeamPrNoticeModalProps) {
  if (!open) return null
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
        aria-labelledby="team-pr-notice-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="team-pr-notice-title" className="modal-title">
            Team 文脈（PR スキル）について
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
          Developer 以外のチーム文脈では、スキルツリーとして{' '}
          <code>agent/skills/pr</code> を読み込みます。スキル本文は Claude Code
          前提の記述が多く、Strands 上ですべてがすぐに期待どおり動くとは限りません。
        </p>
        <div className="composer project-create-actions">
          <button
            type="button"
            className="composer-send"
            disabled={busy}
            onClick={() => onConfirm()}
          >
            理解して続行
          </button>
        </div>
      </div>
    </div>
  )
}
