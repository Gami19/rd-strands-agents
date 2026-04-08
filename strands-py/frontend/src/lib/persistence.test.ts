import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ChatMessage } from '../types/chat'
import {
  emptyProjectPersist,
  isValidProjectId,
  LS_KEY,
  parsePersisted,
  readBootState,
} from './persistence'

describe('isValidProjectId', () => {
  it('accepts allowed characters and length', () => {
    expect(isValidProjectId('a')).toBe(true)
    expect(isValidProjectId('my-project_1.x')).toBe(true)
  })

  it('rejects empty and too long', () => {
    expect(isValidProjectId('')).toBe(false)
    expect(isValidProjectId('a'.repeat(129))).toBe(false)
  })

  it('rejects invalid characters', () => {
    expect(isValidProjectId('あ')).toBe(false)
    expect(isValidProjectId('a/b')).toBe(false)
    expect(isValidProjectId('a b')).toBe(false)
  })
})

describe('emptyProjectPersist', () => {
  it('returns default shape', () => {
    expect(emptyProjectPersist()).toEqual({
      messages: [],
      workspaceQuotes: [],
      agentId: '',
      mode: 'default',
      input: '',
      uploadedRefs: [],
      teamLandingOpen: false,
    })
  })
})

describe('parsePersisted', () => {
  it('handles null and empty', () => {
    expect(parsePersisted(null)).toEqual({
      activeProjectId: 'default',
      byProject: {},
    })
  })

  it('parses valid payload', () => {
    const messages: ChatMessage[] = [
      { id: '1', role: 'user', text: 'hi' },
    ]
    const raw = JSON.stringify({
      activeProjectId: 'proj1',
      byProject: {
        proj1: {
          messages,
          workspaceQuotes: [],
          agentId: 'a1',
          mode: 'skills',
          input: 'x',
          uploadedRefs: [],
          teamLandingOpen: true,
        },
      },
    })
    const p = parsePersisted(raw)
    expect(p.activeProjectId).toBe('proj1')
    expect(p.byProject.proj1?.mode).toBe('skills')
    expect(p.byProject.proj1?.messages).toEqual(messages)
    expect(p.byProject.proj1?.teamLandingOpen).toBe(true)
  })

  it('drops invalid project keys', () => {
    const raw = JSON.stringify({
      activeProjectId: 'default',
      byProject: {
        default: { messages: [], mode: 'default' },
        'bad/id': { messages: [] },
      },
    })
    const p = parsePersisted(raw)
    expect(p.byProject['bad/id']).toBeUndefined()
    expect(p.byProject.default).toBeDefined()
  })

  it('normalizes invalid mode', () => {
    const raw = JSON.stringify({
      activeProjectId: 'default',
      byProject: {
        default: { messages: [], mode: 'nope' },
      },
    })
    expect(parsePersisted(raw).byProject.default?.mode).toBe('default')
  })

  it('returns default on invalid JSON', () => {
    expect(parsePersisted('{').activeProjectId).toBe('default')
  })

  it('falls back activeProjectId when invalid', () => {
    const raw = JSON.stringify({
      activeProjectId: '../x',
      byProject: {},
    })
    expect(parsePersisted(raw).activeProjectId).toBe('default')
  })
})

describe('readBootState', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('uses localStorage when available', () => {
    const data = {
      activeProjectId: 'p1',
      byProject: {
        p1: {
          messages: [],
          workspaceQuotes: [],
          agentId: '',
          mode: 'default',
          input: '',
          uploadedRefs: [],
          teamLandingOpen: false,
        },
      },
    }
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => (k === LS_KEY ? JSON.stringify(data) : null),
    })
    const boot = readBootState()
    expect(boot.activeProjectId).toBe('p1')
    expect(boot.slice.messages).toEqual([])
    expect(boot.vault.p1).toEqual(boot.slice)
  })

  it('returns default vault when localStorage throws', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('blocked')
      },
    })
    const boot = readBootState()
    expect(boot.activeProjectId).toBe('default')
    expect(boot.vault.default).toEqual(emptyProjectPersist())
  })
})
