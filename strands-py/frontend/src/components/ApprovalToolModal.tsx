export type ApprovalToolModalProps = {
  approvalSessionId: string | null
  approvalBusy: boolean
  approvalInterrupts: { id: string; name?: string | null; reason?: unknown }[]
  onDismiss: () => void
  onResume: (approved: boolean) => void
}

export function ApprovalToolModal({
  approvalSessionId,
  approvalBusy,
  approvalInterrupts,
  onDismiss,
  onResume,
}: ApprovalToolModalProps) {
  if (!approvalSessionId) return null
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={() => !approvalBusy && onDismiss()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="approval-modal-title" className="modal-title">
            ツール実行の承認
          </h2>
          <button
            type="button"
            className="modal-close"
            disabled={approvalBusy}
            onClick={onDismiss}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <p className="modal-hint">
          この操作は書き込み/削除系のツール実行を含みます。許可しますか？
        </p>
        <div className="bubble-reasoning">
          {approvalInterrupts[0]?.reason ? (
            <pre style={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(approvalInterrupts[0].reason, null, 2)}
            </pre>
          ) : (
            <span>詳細がありません</span>
          )}
        </div>
        <div className="composer">
          <button
            type="button"
            className="composer-send"
            disabled={approvalBusy}
            onClick={() => void onResume(true)}
          >
            許可
          </button>
          <button
            type="button"
            className="composer-stop"
            disabled={approvalBusy}
            onClick={() => void onResume(false)}
          >
            拒否
          </button>
        </div>
      </div>
    </div>
  )
}
