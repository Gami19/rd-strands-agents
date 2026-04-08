import { describe, expect, it } from 'vitest'
import type { AgentListItem, WorkspaceQuoteRef } from '../types/project'
import {
  agentDisplayNameForId,
  agentYamlDisplayName,
  workspaceQuoteChipLabel,
} from './agentsDisplay'

const agents: AgentListItem[] = [
  { agent_id: 'foo', name: 'Foo Name' },
  { agent_id: 'bar', name: '  ' },
]

describe('agentDisplayNameForId', () => {
  it('uses registered name', () => {
    expect(agentDisplayNameForId('foo', agents)).toBe('Foo Name')
  })

  it('falls back to id', () => {
    expect(agentDisplayNameForId('unknown', agents)).toBe('unknown')
    expect(agentDisplayNameForId('bar', agents)).toBe('bar')
  })
})

describe('agentYamlDisplayName', () => {
  it('returns filename when not yaml', () => {
    expect(agentYamlDisplayName('readme.txt', agents)).toBe('readme.txt')
  })

  it('maps yaml to agent name', () => {
    expect(agentYamlDisplayName('foo.yaml', agents)).toBe('Foo Name')
  })

  it('falls back to filename when id unknown', () => {
    expect(agentYamlDisplayName('baz.yaml', agents)).toBe('baz.yaml')
  })
})

describe('workspaceQuoteChipLabel', () => {
  it('uses yaml display for agents yaml', () => {
    const q: WorkspaceQuoteRef = {
      id: '1',
      area: 'agents',
      filename: 'foo.yaml',
    }
    expect(workspaceQuoteChipLabel(q, agents)).toBe('Foo Name')
  })

  it('uses raw filename otherwise', () => {
    const q: WorkspaceQuoteRef = {
      id: '1',
      area: 'notes',
      filename: 'x.md',
    }
    expect(workspaceQuoteChipLabel(q, agents)).toBe('x.md')
  })
})
