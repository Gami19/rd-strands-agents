import { describe, expect, it } from 'vitest'
import type { ChatMessage } from '../types/chat'
import { buildConversationHistoryPayload, handoffLabel } from './chatPayload'

function msg(
  partial: Pick<ChatMessage, 'id' | 'role' | 'text'> &
    Partial<Omit<ChatMessage, 'id' | 'role' | 'text'>>,
): ChatMessage {
  return { ...partial }
}

describe('handoffLabel', () => {
  it('returns empty for non-handoff', () => {
    expect(
      handoffLabel(msg({ id: '1', role: 'user', text: 'x' })),
    ).toBe('')
  })

  it('formats from and to agents', () => {
    expect(
      handoffLabel(
        msg({
          id: '1',
          role: 'handoff',
          text: '',
          fromAgents: ['a', 'b'],
          toAgents: ['c'],
        }),
      ),
    ).toBe('a, b から c へ引き継ぎ')
  })

  it('formats to-only', () => {
    expect(
      handoffLabel(
        msg({
          id: '1',
          role: 'handoff',
          text: '',
          toAgents: ['x'],
        }),
      ),
    ).toBe('エージェント x に引き継ぎ')
  })

  it('returns default when no agents', () => {
    expect(
      handoffLabel(msg({ id: '1', role: 'handoff', text: '' })),
    ).toBe('引き継ぎ')
  })
})

describe('buildConversationHistoryPayload', () => {
  it('skips handoff and empty text', () => {
    const out = buildConversationHistoryPayload([
      msg({ id: '1', role: 'handoff', text: '' }),
      msg({ id: '2', role: 'user', text: '   ' }),
      msg({ id: '3', role: 'user', text: 'hello' }),
    ])
    expect(out).toEqual([{ role: 'user', content: 'hello' }])
  })

  it('keeps last 40 items', () => {
    const many = Array.from({ length: 45 }, (_, i) =>
      msg({
        id: String(i),
        role: i % 2 === 0 ? 'user' : 'assistant',
        text: `m${i}`,
      }),
    )
    const out = buildConversationHistoryPayload(many)
    expect(out).toHaveLength(40)
    expect(out[0].content).toBe('m5')
    expect(out[39].content).toBe('m44')
  })

  it('truncates very long content', () => {
    const long = 'x'.repeat(120_001)
    const out = buildConversationHistoryPayload([
      msg({ id: '1', role: 'user', text: long }),
    ])
    expect(out).toHaveLength(1)
    expect(out[0].content.length).toBeLessThanOrEqual(120_000 + 30)
    expect(out[0].content).toContain('切り詰め')
  })

  it('joins workspaceTargets prefix with user body for history', () => {
    const out = buildConversationHistoryPayload([
      msg({
        id: '1',
        role: 'user',
        text: 'hello',
        workspaceTargets: [
          {
            id: 'a',
            area: 'proposal',
            filename: 'hiphop_alright.md',
          },
        ],
      }),
    ])
    expect(out).toHaveLength(1)
    expect(out[0].content).toContain('[workspace_target]')
    expect(out[0].content).toContain('hiphop_alright.md')
    expect(out[0].content).toContain('hello')
    expect(out[0].content.indexOf('hello')).toBeGreaterThan(
      out[0].content.indexOf('[/workspace_target]'),
    )
  })

  it('includes workspace-only user turn in history', () => {
    const out = buildConversationHistoryPayload([
      msg({
        id: '1',
        role: 'user',
        text: '',
        workspaceTargets: [
          { id: 'x', area: 'notes', filename: 'a.md' },
        ],
      }),
    ])
    expect(out).toHaveLength(1)
    expect(out[0].content).toContain('notes')
    expect(out[0].content).toContain('a.md')
  })
})
