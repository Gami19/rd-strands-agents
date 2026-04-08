import { formatWorkspaceTargetBlocks } from './workspace'
import type { ChatMessage } from '../types/chat'

export function handoffLabel(m: ChatMessage): string {
  if (m.role !== 'handoff') return ''
  const fr = m.fromAgents?.length ? m.fromAgents.join(', ') : ''
  const to = m.toAgents?.length ? m.toAgents.join(', ') : ''
  if (fr && to) return `${fr} から ${to} へ引き継ぎ`
  if (to) return `エージェント ${to} に引き継ぎ`
  return '引き継ぎ'
}

const MAX_CONVERSATION_HISTORY_ITEMS = 40
const MAX_HISTORY_MESSAGE_CHARS = 120_000

export function buildConversationHistoryPayload(
  msgs: ChatMessage[],
): { role: 'user' | 'assistant'; content: string }[] {
  const out: { role: 'user' | 'assistant'; content: string }[] = []
  for (const m of msgs) {
    if (m.role === 'handoff') continue
    if (m.role !== 'user' && m.role !== 'assistant') continue
    let content: string
    if (m.role === 'user' && m.workspaceTargets?.length) {
      const prefix = formatWorkspaceTargetBlocks(m.workspaceTargets)
      const body = (m.text || '').trim()
      content = body ? `${prefix}${body}` : prefix.replace(/\n+$/, '')
    } else {
      content = (m.text || '').trim()
    }
    if (!content) continue
    if (content.length > MAX_HISTORY_MESSAGE_CHARS) {
      content =
        content.slice(0, MAX_HISTORY_MESSAGE_CHARS) +
        '\n... (表示用に切り詰め)'
    }
    out.push({ role: m.role, content })
  }
  return out.slice(-MAX_CONVERSATION_HISTORY_ITEMS)
}
