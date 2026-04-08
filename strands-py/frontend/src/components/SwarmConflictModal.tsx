export type SwarmConflictModalProps = {
  open: boolean
  onClose: () => void
}

export function SwarmConflictModal({ open, onClose }: SwarmConflictModalProps) {
  if (!open) return null
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="swarm-agents-conflict-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="swarm-agents-conflict-title" className="modal-title">
            Swarm モード
          </h2>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <p className="modal-hint">
          Swarm ではタスクに応じてエージェントがマルチエージェントシステムを組み立てます。agents
          の YAML を複数参照してマルチエージェントを起動する場合は、モードを「スキル（自動選択）」に切り替えてください。
        </p>
        <div className="composer">
          <button
            type="button"
            className="composer-send"
            onClick={onClose}
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  )
}
