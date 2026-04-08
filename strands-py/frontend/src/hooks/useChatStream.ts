import type { Dispatch, SetStateAction } from 'react'
import { useCallback, useRef, useState } from 'react'
import { buildConversationHistoryPayload } from '../lib/chatPayload'
import {
  feedSseLines,
  streamMetaFromPayload,
  tryParseDataLine,
} from '../lib/streamSse'
import { formatApiDetail } from '../lib/apiDetail'
import {
  dedupeAgentIdsFromQuotes,
  formatWorkspaceTargetBlocks,
  isAgentsYamlRef,
} from '../lib/workspace'
import type { ChatMessage, ChatMode, StreamPayload, ToolTraceEntry } from '../types/chat'
import type { UploadedRef, WorkspaceQuoteRef } from '../types/project'

export type ApprovalInterrupt = {
  id: string
  name?: string | null
  reason?: unknown
}

export type UseChatStreamParams = {
  setError: Dispatch<SetStateAction<string | null>>
  messages: ChatMessage[]
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
  input: string
  setInput: Dispatch<SetStateAction<string>>
  workspaceQuotes: WorkspaceQuoteRef[]
  setWorkspaceQuotes: Dispatch<SetStateAction<WorkspaceQuoteRef[]>>
  uploadedRefs: UploadedRef[]
  mode: ChatMode
  agentId: string
  activeProjectId: string
  loadArtifacts: () => Promise<void>
  loadAgents: () => Promise<void>
  scrollToBottom: () => void
  autoResizeComposer: () => void
  setSwarmAgentsConflictOpen: Dispatch<SetStateAction<boolean>>
}

export function useChatStream({
  setError,
  messages,
  setMessages,
  input,
  setInput,
  workspaceQuotes,
  setWorkspaceQuotes,
  uploadedRefs,
  mode,
  agentId,
  activeProjectId,
  loadArtifacts,
  loadAgents,
  scrollToBottom,
  autoResizeComposer,
  setSwarmAgentsConflictOpen,
}: UseChatStreamParams) {
  const [streaming, setStreaming] = useState(false)
  const [streamAssistantId, setStreamAssistantId] = useState<string | null>(
    null,
  )
  const [approvalSessionId, setApprovalSessionId] = useState<string | null>(
    null,
  )
  const [approvalInterrupts, setApprovalInterrupts] = useState<
    ApprovalInterrupt[]
  >([])
  const [approvalBusy, setApprovalBusy] = useState(false)

  const assistantIdRef = useRef<string | null>(null)
  const chatAbortRef = useRef<AbortController | null>(null)

  const clearApprovalAndError = useCallback(() => {
    setError(null)
    setApprovalSessionId(null)
    setApprovalInterrupts([])
  }, [setError])

  const applyStreamPayload = useCallback((payload: StreamPayload) => {
    if (payload.type === 'error') {
      if (payload.code === 'cancelled') {
        setError('送信を中止しました')
        return
      }
      setError(payload.message)
      return
    }

    if (payload.type === 'done') {
      return
    }

    if (payload.type === 'interrupt') {
      setApprovalSessionId(payload.session_id)
      setApprovalInterrupts(
        Array.isArray(payload.interrupts) ? payload.interrupts : [],
      )
      return
    }

    if (payload.type === 'handoff') {
      const newAssistantId = crypto.randomUUID()
      assistantIdRef.current = newAssistantId
      setStreamAssistantId(newAssistantId)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'handoff',
          text: '',
          fromAgents: [...payload.from_agents],
          toAgents: [...payload.to_agents],
          handoffMessage: payload.message ?? undefined,
        },
        {
          id: newAssistantId,
          role: 'assistant',
          text: '',
          reasoning: '',
          toolTrace: [],
        },
      ])
      return
    }

    const id = assistantIdRef.current
    if (!id) return

    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== id) return m
        const meta = streamMetaFromPayload(payload)
        let next: ChatMessage = m
        if (payload.type === 'text') {
          next = { ...next, text: next.text + payload.content }
        } else if (payload.type === 'reasoning') {
          next = {
            ...next,
            reasoning: (next.reasoning ?? '') + payload.content,
          }
        } else if (payload.type === 'tool') {
          const entry: ToolTraceEntry = { name: payload.name }
          if (typeof payload.stream_revision === 'number') {
            entry.stream_revision = payload.stream_revision
          }
          if ('input' in payload) {
            entry.input = payload.input
          }
          next = {
            ...next,
            toolTrace: [...(next.toolTrace ?? []), entry],
          }
        }
        if (meta && (meta.phase !== undefined || meta.agent !== undefined)) {
          next = {
            ...next,
            streamContext: { ...next.streamContext, ...meta },
          }
        }
        return next
      }),
    )
  }, [setError, setMessages])

  const stopStreaming = useCallback(() => {
    chatAbortRef.current?.abort()
    chatAbortRef.current = null
  }, [])

  const send = useCallback(async () => {
    const multiIds = dedupeAgentIdsFromQuotes(workspaceQuotes)
    if (mode === 'swarm' && multiIds.length >= 2) {
      setSwarmAgentsConflictOpen(true)
      return
    }
    const multiAgentMode = mode === 'skills' && multiIds.length >= 2
    const quotesForPrefix = multiAgentMode
      ? workspaceQuotes.filter((q) => !isAgentsYamlRef(q))
      : workspaceQuotes
    const prefix = formatWorkspaceTargetBlocks(quotesForPrefix)
    const body = input.trim()
    const apiMessage = body ? `${prefix}${body}` : prefix.replace(/\n+$/, '')
    if (!apiMessage || streaming) return
    const fileWorkspaceTargets = quotesForPrefix.filter(
      (q) => !isAgentsYamlRef(q),
    )

    const ac = new AbortController()
    chatAbortRef.current = ac

    setError(null)
    setInput('')
    setWorkspaceQuotes([])
    requestAnimationFrame(autoResizeComposer)
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: body,
      ...(fileWorkspaceTargets.length
        ? { workspaceTargets: fileWorkspaceTargets }
        : {}),
      ...(multiAgentMode
        ? { multiAgentIds: [...multiIds] }
        : mode === 'skills' && agentId.trim()
          ? { selectedAgentId: agentId.trim() }
          : {}),
    }
    const assistantId = crypto.randomUUID()
    assistantIdRef.current = assistantId
    setStreamAssistantId(assistantId)
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      text: '',
      reasoning: '',
      toolTrace: [],
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setStreaming(true)
    scrollToBottom()

    try {
      const attachmentPayload =
        uploadedRefs.length > 0
          ? uploadedRefs.map((r) => ({
              kind: r.kind,
              filename: r.filename,
              url: r.url,
            }))
          : undefined
      const conversationHistory = buildConversationHistoryPayload(messages)
      const historyField =
        conversationHistory.length > 0
          ? { conversation_history: conversationHistory }
          : {}
      const res = await fetch(
        multiAgentMode ? '/api/chat/agents-multi' : '/api/chat',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(
            multiAgentMode
              ? {
                  message: apiMessage,
                  project_id: activeProjectId,
                  agent_ids: multiIds,
                  attachments: attachmentPayload,
                  ...historyField,
                }
              : {
                  message: apiMessage,
                  mode,
                  project_id: activeProjectId,
                  ...((mode === 'skills' || mode === 'workflow') && agentId
                    ? { agent_id: agentId }
                    : {}),
                  attachments: attachmentPayload,
                  ...historyField,
                },
          ),
          signal: ac.signal,
        },
      )

      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          detail?: unknown
        }
        const msg = formatApiDetail(
          data.detail,
          res.statusText || 'リクエストに失敗しました',
        )
        throw new Error(msg || 'リクエストに失敗しました')
      }

      const reader = res.body?.getReader()
      if (!reader) throw new Error('ストリームを読めませんでした')

      const decoder = new TextDecoder()
      let lineBuf = ''

      const onPayload = (ev: StreamPayload) => {
        applyStreamPayload(ev)
      }

      while (true) {
        const { done, value } = await reader.read()
        const chunk = decoder.decode(value ?? new Uint8Array(), {
          stream: !done,
        })
        lineBuf = feedSseLines(lineBuf, chunk, onPayload)
        scrollToBottom()
        if (done) break
      }

      const tail = tryParseDataLine(lineBuf.trim())
      if (tail) onPayload(tail)
    } catch (e) {
      const aborted =
        (e instanceof DOMException && e.name === 'AbortError') ||
        (e instanceof Error && e.name === 'AbortError')
      if (aborted) {
        setError('送信を中止しました')
      } else {
        setError(e instanceof Error ? e.message : 'エラーが発生しました')
      }
    } finally {
      chatAbortRef.current = null
      assistantIdRef.current = null
      setStreamAssistantId(null)
      setStreaming(false)
      scrollToBottom()
      void loadArtifacts()
      void loadAgents()
    }
  }, [
    input,
    workspaceQuotes,
    streaming,
    mode,
    uploadedRefs,
    messages,
    scrollToBottom,
    applyStreamPayload,
    agentId,
    activeProjectId,
    loadArtifacts,
    loadAgents,
    autoResizeComposer,
    setError,
    setInput,
    setWorkspaceQuotes,
    setMessages,
    setSwarmAgentsConflictOpen,
  ])

  const resumeWithApproval = useCallback(
    async (approved: boolean) => {
      const sessionId = approvalSessionId
      if (!sessionId || approvalBusy || streaming) return
      const first = approvalInterrupts[0]
      if (!first?.id) return

      setApprovalBusy(true)
      setError(null)
      setStreaming(true)
      scrollToBottom()

      try {
        const res = await fetch('/api/chat/resume', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            interrupt_responses: [
              {
                interruptResponse: {
                  interruptId: first.id,
                  response: approved ? 'y' : 'n',
                },
              },
            ],
          }),
        })

        if (!res.ok) {
          const data = (await res.json().catch(() => ({}))) as {
            detail?: unknown
          }
          throw new Error(
            formatApiDetail(
              data.detail,
              res.statusText || 'リクエストに失敗しました',
            ),
          )
        }

        const reader = res.body?.getReader()
        if (!reader) throw new Error('ストリームを読めませんでした')

        const decoder = new TextDecoder()
        let lineBuf = ''
        const onPayload = (ev: StreamPayload) => {
          applyStreamPayload(ev)
        }
        while (true) {
          const { done, value } = await reader.read()
          const chunk = decoder.decode(value ?? new Uint8Array(), {
            stream: !done,
          })
          lineBuf = feedSseLines(lineBuf, chunk, onPayload)
          scrollToBottom()
          if (done) break
        }
        const tail = tryParseDataLine(lineBuf.trim())
        if (tail) onPayload(tail)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'エラーが発生しました')
      } finally {
        setApprovalBusy(false)
        setApprovalSessionId(null)
        setApprovalInterrupts([])
        setStreaming(false)
        scrollToBottom()
        void loadArtifacts()
        void loadAgents()
      }
    },
    [
      approvalSessionId,
      approvalInterrupts,
      approvalBusy,
      streaming,
      scrollToBottom,
      applyStreamPayload,
      loadArtifacts,
      loadAgents,
      setError,
    ],
  )

  return {
    streaming,
    streamAssistantId,
    approvalSessionId,
    setApprovalSessionId,
    approvalInterrupts,
    approvalBusy,
    stopStreaming,
    send,
    resumeWithApproval,
    clearApprovalAndError,
  }
}
