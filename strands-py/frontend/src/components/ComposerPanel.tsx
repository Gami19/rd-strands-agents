import type { Dispatch, RefObject, SetStateAction } from 'react'
import {
  dedupeAgentIdsFromQuotes,
  dedupeAgentYamlQuotesForDisplay,
  isAgentsYamlRef,
} from '../lib/workspace'
import { workspaceQuoteChipLabel } from '../lib/agentsDisplay'
import type { TeamContextId } from '../lib/teamContext'
import type { ChatMode } from '../types/chat'
import type { AgentListItem, UploadedRef, WorkspaceQuoteRef } from '../types/project'
import { AttachFileModal } from './AttachFileModal'
import { SwarmConflictModal } from './SwarmConflictModal'

function agentGroupsForSelect(
  agents: AgentListItem[],
  useGroups: boolean,
): { label: string; items: AgentListItem[] }[] {
  if (!useGroups) {
    return [{ label: '', items: [...agents].sort((a, b) => a.name.localeCompare(b.name, 'ja')) }]
  }
  const map = new Map<string, AgentListItem[]>()
  for (const a of agents) {
    const d =
      typeof a.department === 'string' && a.department.trim()
        ? a.department.trim()
        : 'メンバー'
    const list = map.get(d) ?? []
    list.push(a)
    map.set(d, list)
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b, 'ja'))
    .map(([label, items]) => ({
      label,
      items: items.sort((x, y) => x.name.localeCompare(y.name, 'ja')),
    }))
}

function optionLabel(a: AgentListItem): string {
  const desc =
    typeof a.description === 'string' && a.description.trim()
      ? a.description.trim()
      : ''
  if (!desc) return a.name
  const short = desc.length > 48 ? `${desc.slice(0, 48)}…` : desc
  return `${a.name} — ${short}`
}

export type ComposerPanelProps = {
  streaming: boolean
  workflowAllowed: boolean
  activeTeamContext: TeamContextId
  mode: ChatMode
  setMode: Dispatch<SetStateAction<ChatMode>>
  agentId: string
  setAgentId: (v: string) => void
  agents: AgentListItem[]
  agentsLoading: boolean
  agentsError: string | null
  uploadedRefs: UploadedRef[]
  workspaceQuotes: WorkspaceQuoteRef[]
  removeWorkspaceQuote: (id: string) => void
  input: string
  setInput: (v: string) => void
  composerTextareaRef: RefObject<HTMLTextAreaElement | null>
  fileInputRef: RefObject<HTMLInputElement | null>
  attachModalOpen: boolean
  setAttachModalOpen: (v: boolean) => void
  uploadBusy: boolean
  uploadFiles: (files: FileList | null) => void
  swarmAgentsConflictOpen: boolean
  setSwarmAgentsConflictOpen: (v: boolean) => void
  send: () => void
  stopStreaming: () => void
  setWorkspaceQuotes: Dispatch<SetStateAction<WorkspaceQuoteRef[]>>
}

export function ComposerPanel({
  streaming,
  workflowAllowed,
  activeTeamContext,
  mode,
  setMode,
  agentId,
  setAgentId,
  agents,
  agentsLoading,
  agentsError,
  uploadedRefs,
  workspaceQuotes,
  removeWorkspaceQuote,
  input,
  setInput,
  composerTextareaRef,
  fileInputRef,
  attachModalOpen,
  setAttachModalOpen,
  uploadBusy,
  uploadFiles,
  swarmAgentsConflictOpen,
  setSwarmAgentsConflictOpen,
  send,
  stopStreaming,
  setWorkspaceQuotes,
}: ComposerPanelProps) {
  const teamMemberUi = activeTeamContext !== 'developer'
  const agentGroups = agentGroupsForSelect(agents, teamMemberUi)

  return (
    <div className="composer-wrap">
      <div className="composer-toolbar">
        <div className="composer-toolbar-row">
          <button
            type="button"
            className={`mode-switch ${
              mode === 'skills'
                ? 'skills'
                : mode === 'workflow'
                  ? 'workflow'
                  : mode === 'swarm'
                    ? 'swarm'
                    : 'default'
            }`}
            disabled={streaming}
            onClick={() =>
              setMode((prev) => {
                if (workflowAllowed) {
                  if (prev === 'default') return 'skills'
                  if (prev === 'skills') return 'workflow'
                  if (prev === 'workflow') return 'swarm'
                  return 'default'
                }
                if (prev === 'default') return 'skills'
                if (prev === 'skills') return 'swarm'
                return 'default'
              })
            }
            aria-pressed={mode !== 'default'}
            aria-label={
              mode === 'default'
                ? 'チャットモード: Skillなし。クリックでスキル（自動選択）へ'
                : mode === 'skills'
                  ? 'チャットモード: スキル（自動選択）。' +
                    (workflowAllowed
                      ? 'クリックで Workflow へ'
                      : 'クリックで Swarm へ')
                  : mode === 'workflow'
                    ? 'チャットモード: Workflow。クリックで Swarm へ'
                    : 'チャットモード: Swarm。クリックで通常モードへ'
            }
            title={
              mode === 'default'
                ? 'クリックでスキル（自動選択）に切り替え'
                : mode === 'skills'
                  ? workflowAllowed
                    ? 'クリックで Workflow に切り替え'
                    : 'クリックで Swarm に切り替え'
                  : mode === 'workflow'
                    ? 'クリックで Swarm に切り替え'
                    : 'クリックで通常モードに戻す'
            }
          >
            {mode === 'skills'
              ? 'スキル（自動選択）'
              : mode === 'workflow'
                ? 'Workflow'
                : mode === 'swarm'
                  ? 'Swarm'
                  : 'Skillなし'}
          </button>
          {mode === 'skills' &&
          dedupeAgentIdsFromQuotes(workspaceQuotes).length < 2 ? (
            <select
              className={`mode-switch ${
                teamMemberUi && agentId ? 'mode-switch-agent-emphasis' : ''
              }`}
              disabled={streaming || agentsLoading}
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              aria-label={
                teamMemberUi
                  ? 'チームの AI メンバー（エージェント）を選択'
                  : 'エージェントを選択'
              }
              title={
                teamMemberUi
                  ? '部門に紐づく AI アシスタント。各エージェントは 1 スキルに対応します'
                  : 'エージェントを選択'
              }
            >
              <option value="">
                {agentsLoading
                  ? '読み込み中…'
                  : agentsError
                    ? agentsError
                    : agents.length
                      ? teamMemberUi
                        ? 'メンバーを選択…'
                        : '（未選択は自動エージェントを選べます）'
                      : teamMemberUi
                        ? '既定メンバーがありません（workspace の agents を確認）'
                        : 'エージェントなし'}
              </option>
              {teamMemberUi
                ? agentGroups.map((g) =>
                    g.label ? (
                      <optgroup key={g.label} label={g.label}>
                        {g.items.map((a) => (
                          <option key={a.agent_id} value={a.agent_id}>
                            {optionLabel(a)}
                          </option>
                        ))}
                      </optgroup>
                    ) : (
                      g.items.map((a) => (
                        <option key={a.agent_id} value={a.agent_id}>
                          {optionLabel(a)}
                        </option>
                      ))
                    ),
                  )
                : agents.map((a) => (
                    <option key={a.agent_id} value={a.agent_id}>
                      {a.name}
                    </option>
                  ))}
            </select>
          ) : null}
          {mode === 'workflow' ? (
            <select
              className="mode-switch"
              disabled={streaming}
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              aria-label="Workflow を選択"
              title="Workflow を選択"
            >
              <option value="convert-pdf">convert-pdf</option>
              <option value="architecture-design-workflow">
                architecture-design-workflow
              </option>
              <option value="engineering-workflow">engineering-workflow</option>
            </select>
          ) : null}
          <div className="uploaded-marks" aria-label="アップロード済みファイル">
            {uploadedRefs.map((r) => (
              <a
                key={r.id}
                href={r.url}
                target="_blank"
                rel="noreferrer"
                className={`file-mark file-mark-${r.kind}`}
                title={r.filename}
              >
                <span className="file-mark-icon" aria-hidden>
                  <svg
                    width="14"
                    height="18"
                    viewBox="0 0 14 18"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M1 0h8l4 4v13a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V1a1 1 0 0 1 1-1z"
                      stroke="currentColor"
                      strokeWidth="1.2"
                      fill="none"
                    />
                    <path
                      d="M9 0v4h4"
                      stroke="currentColor"
                      strokeWidth="1.2"
                      fill="none"
                    />
                  </svg>
                </span>
                <span className="file-mark-ext">
                  {r.filename.includes('.')
                    ? r.filename.slice(r.filename.lastIndexOf('.'))
                    : ''}
                </span>
              </a>
            ))}
          </div>
          <button
            type="button"
            className="attach-page-btn"
            disabled={streaming}
            onClick={() => setAttachModalOpen(true)}
            aria-label="ファイルを添付"
            title="添付（.md / .pdf / .png / .jpeg）"
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M14 2v6h6"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.pdf,.png,.jpg,.jpeg,.ts,.tsx,.js,.py,.ipynb,application/pdf,text/markdown,image/png,image/jpeg,application/x-ipynb+json,text/plain"
          className="attach-input-hidden"
          onChange={(e) => {
            void uploadFiles(e.target.files)
            e.target.value = ''
          }}
        />
      </div>
      <AttachFileModal
        open={attachModalOpen}
        uploadBusy={uploadBusy}
        fileInputRef={fileInputRef}
        onClose={() => setAttachModalOpen(false)}
        onUploadFiles={uploadFiles}
      />
      <SwarmConflictModal
        open={swarmAgentsConflictOpen}
        onClose={() => setSwarmAgentsConflictOpen(false)}
      />
      <div className="composer">
        <div className="composer-field">
          {workspaceQuotes.length > 0 ? (
            <div
              className="composer-quotes"
              aria-label="送信に含まれる workspace 参照"
            >
              {mode === 'skills' &&
              dedupeAgentIdsFromQuotes(workspaceQuotes).length >= 2 ? (
                <>
                  <div
                    className="composer-quotes-multi"
                    role="group"
                    aria-label="マルチエージェントシステムとして結合したエージェント定義"
                  >
                    <span className="composer-quotes-multi-label">
                      マルチエージェント
                    </span>
                    <div className="composer-quotes-multi-chain">
                      {dedupeAgentYamlQuotesForDisplay(workspaceQuotes).map(
                        (q, idx) => (
                          <div key={q.id} className="composer-quotes-multi-item">
                            {idx > 0 ? (
                              <span
                                className="composer-quotes-multi-join"
                                aria-hidden="true"
                              >
                                +
                              </span>
                            ) : null}
                            <div className="composer-quote composer-quote-multi">
                              <button
                                type="button"
                                className="composer-quote-remove"
                                onClick={() => removeWorkspaceQuote(q.id)}
                                aria-label={`参照 ${workspaceQuoteChipLabel(q, agents)} を削除`}
                                title="この参照を削除"
                              >
                                ×
                              </button>
                              <div className="composer-quote-body">
                                <span className="composer-quote-filename">
                                  {workspaceQuoteChipLabel(q, agents)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                  {workspaceQuotes
                    .filter((q) => !isAgentsYamlRef(q))
                    .map((q) => (
                      <div key={q.id} className="composer-quote">
                        <button
                          type="button"
                          className="composer-quote-remove"
                          onClick={() => removeWorkspaceQuote(q.id)}
                          aria-label={`参照 ${q.area}/${q.filename} を削除`}
                          title="この参照を削除"
                        >
                          ×
                        </button>
                        <div className="composer-quote-body">
                          <span className="composer-quote-filename">
                            {q.filename}
                          </span>
                        </div>
                      </div>
                    ))}
                </>
              ) : (
                workspaceQuotes.map((q) => (
                  <div key={q.id} className="composer-quote">
                    <button
                      type="button"
                      className="composer-quote-remove"
                      onClick={() => removeWorkspaceQuote(q.id)}
                      aria-label={`参照 ${workspaceQuoteChipLabel(q, agents)} を削除`}
                      title="この参照を削除"
                    >
                      ×
                    </button>
                    <div className="composer-quote-body">
                      <span className="composer-quote-filename">
                        {workspaceQuoteChipLabel(q, agents)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : null}
          <textarea
            className="composer-input"
            rows={1}
            placeholder="メッセージを入力…"
            value={input}
            disabled={streaming}
            ref={composerTextareaRef}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (
                e.key === 'Backspace' &&
                !streaming &&
                workspaceQuotes.length > 0 &&
                input === ''
              ) {
                const ta = composerTextareaRef.current
                if (
                  ta &&
                  ta.selectionStart === 0 &&
                  ta.selectionEnd === 0
                ) {
                  e.preventDefault()
                  setWorkspaceQuotes((prev) => prev.slice(0, -1))
                  return
                }
              }
              if (
                e.key === 'Enter' &&
                !e.shiftKey &&
                !e.nativeEvent.isComposing &&
                e.nativeEvent.keyCode !== 229
              ) {
                e.preventDefault()
                void send()
              }
            }}
          />
        </div>
        {streaming ? (
          <button
            type="button"
            className="composer-stop"
            onClick={() => stopStreaming()}
          >
            中止
          </button>
        ) : (
          <button
            type="button"
            className="composer-send"
            disabled={!input.trim() && workspaceQuotes.length === 0}
            onClick={() => void send()}
          >
            送信
          </button>
        )}
      </div>
    </div>
  )
}
