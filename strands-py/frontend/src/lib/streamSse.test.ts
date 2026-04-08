import { describe, expect, it, vi } from 'vitest'
import {
  feedSseLines,
  streamMetaFromPayload,
  tryParseDataLine,
} from './streamSse'

describe('tryParseDataLine', () => {
  it('parses SSE data line with JSON payload', () => {
    const p = tryParseDataLine('data: {"type":"text","content":"hi"}')
    expect(p).toEqual({ type: 'text', content: 'hi' })
  })

  it('trims whitespace', () => {
    const p = tryParseDataLine('  data: {"type":"done","stop_reason":null}  ')
    expect(p).toEqual({ type: 'done', stop_reason: null })
  })

  it('returns null for non-data lines', () => {
    expect(tryParseDataLine('event: ping')).toBeNull()
    expect(tryParseDataLine('')).toBeNull()
  })

  it('returns null for empty data payload', () => {
    expect(tryParseDataLine('data:')).toBeNull()
    expect(tryParseDataLine('data:   ')).toBeNull()
  })

  it('returns null for invalid JSON', () => {
    expect(tryParseDataLine('data: not-json')).toBeNull()
  })
})

describe('streamMetaFromPayload', () => {
  it('returns phase and agent when present', () => {
    expect(
      streamMetaFromPayload({
        type: 'text',
        content: 'x',
        phase: 'p1',
        agent: 'a1',
      }),
    ).toEqual({ phase: 'p1', agent: 'a1' })
  })

  it('returns null for done, error, handoff', () => {
    expect(streamMetaFromPayload({ type: 'done', stop_reason: null })).toBeNull()
    expect(
      streamMetaFromPayload({ type: 'error', message: 'e' }),
    ).toBeNull()
    expect(
      streamMetaFromPayload({
        type: 'handoff',
        from_agents: [],
        to_agents: [],
      }),
    ).toBeNull()
  })

  it('returns null when neither phase nor agent', () => {
    expect(streamMetaFromPayload({ type: 'text', content: 'x' })).toBeNull()
  })
})

describe('feedSseLines', () => {
  it('invokes onPayload per complete line and returns remainder', () => {
    const fn = vi.fn()
    const rest = feedSseLines('', 'data: {"type":"text","content":"a"}\ndata:', fn)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn.mock.calls[0][0]).toEqual({ type: 'text', content: 'a' })
    expect(rest).toBe('data:')
  })

  it('accumulates buffer across chunks', () => {
    const fn = vi.fn()
    let buf = feedSseLines('', 'data: {"type":"text","content":"x"}', fn)
    expect(fn).toHaveBeenCalledTimes(0)
    buf = feedSseLines(buf, '\n', fn)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(buf).toBe('')
  })

  it('handles CRLF by splitting on LF only', () => {
    const fn = vi.fn()
    feedSseLines('', 'data: {"type":"text","content":"x"}\r\n', fn)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
