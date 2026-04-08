import type { RefObject } from 'react'

export type AttachFileModalProps = {
  open: boolean
  uploadBusy: boolean
  fileInputRef: RefObject<HTMLInputElement | null>
  onClose: () => void
  onUploadFiles: (files: FileList | null) => void
}

export function AttachFileModal({
  open,
  uploadBusy,
  fileInputRef,
  onClose,
  onUploadFiles,
}: AttachFileModalProps) {
  if (!open) return null
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={() => !uploadBusy && onClose()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="attach-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="attach-modal-title" className="modal-title">
            ファイルを添付
          </h2>
          <button
            type="button"
            className="modal-close"
            disabled={uploadBusy}
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>
        <p className="modal-hint">
          クリックで選択、またはここに .md / .pdf / .png / .jpeg をドロップ
        </p>
        <div
          role="button"
          tabIndex={0}
          className={`modal-dropzone ${uploadBusy ? 'busy' : ''}`}
          onClick={() => !uploadBusy && fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (uploadBusy) return
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              fileInputRef.current?.click()
            }
          }}
          onDragOver={(e) => {
            e.preventDefault()
            e.stopPropagation()
          }}
          onDrop={(e) => {
            e.preventDefault()
            e.stopPropagation()
            void onUploadFiles(e.dataTransfer.files)
          }}
        >
          {uploadBusy ? 'アップロード中…' : 'ファイルを選択'}
        </div>
      </div>
    </div>
  )
}
