import { useEffect, useRef, useState, type RefObject } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { agentDisplayNameForId } from '../lib/agentsDisplay'
import { handoffLabel } from '../lib/chatPayload'
import type { ChatMessage } from '../types/chat'
import type { AgentListItem } from '../types/project'
import type { CopyTextOptions } from '../hooks/useCopyText'

const COPY_LABEL_RESET_MS = 1500

export type ChatThreadProps = {
  listRef: RefObject<HTMLDivElement | null>
  messages: ChatMessage[]
  agents: AgentListItem[]
  streaming: boolean
  streamAssistantId: string | null
  onCopyMessage: (text: string, options?: CopyTextOptions) => Promise<boolean>
}

export function ChatThread({
  listRef,
  messages,
  agents,
  streaming,
  streamAssistantId,
  onCopyMessage,
}: ChatThreadProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const copyResetTimerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (copyResetTimerRef.current !== null) {
        window.clearTimeout(copyResetTimerRef.current)
        copyResetTimerRef.current = null
      }
    }
  }, [])

  return (
    <div className="thread" ref={listRef}>
      {messages.length === 0 && (
        <div className="empty">
          <h1 className="empty-title">何でも聞いてください</h1>
          <p className="empty-hint">
            応答は Server-Sent Events でストリーミング表示されます。AWS
            設定は strands-py/backend/.env を参照してください。
          </p>
        </div>
      )}
      {messages.map((m) =>
        m.role === 'handoff' ? (
          <div key={m.id} className="bubble-row handoff">
            <div className="handoff-ribbon" role="status">
              <span className="handoff-line" aria-hidden />
              <div className="handoff-body">
                <span className="handoff-main">{handoffLabel(m)}</span>
                {m.handoffMessage ? (
                  <span className="handoff-msg">{m.handoffMessage}</span>
                ) : null}
              </div>
              <span className="handoff-line" aria-hidden />
            </div>
          </div>
        ) : (
          <div
            key={m.id}
            className={`bubble-row ${m.role === 'user' ? 'user' : 'assistant'}`}
          >
            {m.role === 'user' ? (
              <div className="bubble-user-column">
                {m.multiAgentIds && m.multiAgentIds.length >= 2 ? (
                  <div
                    className="bubble-user-request-meta bubble-user-request-meta--multi"
                    aria-label="マルチエージェントリクエスト"
                  >
                    <div className="bubble-user-request-head">
                      <span className="bubble-user-request-badge">
                        マルチエージェント
                      </span>
                    </div>
                    <ul className="bubble-user-agent-chips">
                      {m.multiAgentIds.map((aid) => (
                        <li
                          key={aid}
                          className="bubble-user-agent-chip"
                          title={aid}
                        >
                          <span className="bubble-user-agent-chip-name">
                            {agentDisplayNameForId(aid, agents)}
                          </span>
                          <span className="bubble-user-agent-chip-id">{aid}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {m.selectedAgentId &&
                (!m.multiAgentIds || m.multiAgentIds.length < 2) ? (
                  <div
                    className="bubble-user-request-meta bubble-user-request-meta--single"
                    aria-label="選択エージェント"
                  >
                    <div className="bubble-user-request-head">
                      <span className="bubble-user-request-badge">
                        エージェント
                      </span>
                    </div>
                    <ul className="bubble-user-agent-chips">
                      <li
                        className="bubble-user-agent-chip"
                        title={m.selectedAgentId}
                      >
                        <span className="bubble-user-agent-chip-name">
                          {agentDisplayNameForId(m.selectedAgentId, agents)}
                        </span>
                        <span className="bubble-user-agent-chip-id">
                          {m.selectedAgentId}
                        </span>
                      </li>
                    </ul>
                  </div>
                ) : null}
                <div className="bubble">
                  <div className="bubble-text">{m.text}</div>
                </div>
                {m.workspaceTargets?.length ? (
                  <div
                    className="bubble-user-workspace-meta"
                    aria-label="ワークスペース参照"
                  >
                    <div className="bubble-user-request-head">
                      <span className="bubble-user-request-badge">
                        ワークスペース
                      </span>
                    </div>
                    <ul className="bubble-user-workspace-chips">
                      {m.workspaceTargets.map((q) => (
                        <li
                          key={q.id}
                          className="bubble-user-workspace-chip"
                          title={`${q.area}/${q.filename}`}
                        >
                          <span className="bubble-user-workspace-area">
                            {q.area}
                          </span>
                          <span className="bubble-user-workspace-filename">
                            {q.filename}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="bubble">
                <div className="bubble-head">
                  {m.streamContext?.phase || m.streamContext?.agent ? (
                    <div className="bubble-stream-context">
                      {[m.streamContext?.phase, m.streamContext?.agent]
                        .filter(Boolean)
                        .join(' · ')}
                    </div>
                  ) : (
                    <div />
                  )}
                  <button
                    type="button"
                    className="bubble-copy"
                    onClick={() => {
                      void (async () => {
                        const ok = await onCopyMessage(m.text, {
                          skipSuccessToast: true,
                        })
                        if (!ok) return
                        if (copyResetTimerRef.current !== null) {
                          window.clearTimeout(copyResetTimerRef.current)
                        }
                        setCopiedMessageId(m.id)
                        copyResetTimerRef.current = window.setTimeout(() => {
                          setCopiedMessageId(null)
                          copyResetTimerRef.current = null
                        }, COPY_LABEL_RESET_MS)
                      })()
                    }}
                    title={
                      copiedMessageId === m.id ? 'コピーしました' : 'コピー'
                    }
                    aria-label={
                      copiedMessageId === m.id
                        ? 'コピーしました'
                        : 'このメッセージをコピー'
                    }
                  >
                    {copiedMessageId === m.id ? 'コピーしました' : 'コピー'}
                  </button>
                </div>
                {m.reasoning ? (
                  <div className="bubble-reasoning">{m.reasoning}</div>
                ) : null}
                {m.toolTrace?.length ? (
                  <ul className="bubble-tools" aria-label="ツール実行">
                    {m.toolTrace.map((t, i) => {
                      const tk = `${m.id}-tool-${i}-${t.name}-${t.stream_revision ?? i}`
                      const hasInput = t.input !== undefined
                      const inputText = hasInput
                        ? typeof t.input === 'string'
                          ? t.input === ''
                            ? '(input 空)'
                            : t.input
                          : JSON.stringify(t.input, null, 2)
                        : ''
                      const summaryMain = (
                        <span className="bubble-tool-summary-main">
                          <span className="bubble-tool-summary-eyebrow">
                            ツール呼び出し
                          </span>
                          <span className="bubble-tool-summary-name">{t.name}</span>
                          {typeof t.stream_revision === 'number' ? (
                            <span className="bubble-tool-summary-rev">
                              rev {t.stream_revision}
                            </span>
                          ) : null}
                        </span>
                      )
                      return (
                        <li key={tk} className="bubble-tool-item">
                          {hasInput ? (
                            <details className="bubble-tool-acc">
                              <summary className="bubble-tool-summary">
                                <span
                                  className="bubble-tool-summary-chevron"
                                  aria-hidden
                                />
                                {summaryMain}
                              </summary>
                              <div className="bubble-tool-detail">
                                <div className="bubble-tool-detail-caption">
                                  ツールへ渡した値（リクエスト）
                                </div>
                                <pre className="bubble-tool-input">{inputText}</pre>
                              </div>
                            </details>
                          ) : (
                            <div
                              className="bubble-tool-summary bubble-tool-summary-static"
                              aria-label={`ツール ${t.name}`}
                            >
                              {summaryMain}
                              <span className="bubble-tool-summary-hint bubble-tool-summary-hint-muted">
                                引数なし
                              </span>
                            </div>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                ) : null}
                <div className="bubble-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                  {streaming && m.id === streamAssistantId ? (
                    <span className="cursor-blink" aria-hidden />
                  ) : null}
                </div>
              </div>
            )}
          </div>
        ),
      )}
    </div>
  )
}
