import { describe, expect, it } from 'vitest'
import type { WorkspaceQuoteRef } from '../types/project'
import {
  agentIdFromAgentsFilename,
  dedupeAgentIdsFromQuotes,
  dedupeAgentYamlQuotesForDisplay,
  formatWorkspaceTargetBlocks,
  isAgentsYamlRef,
  WORKSPACE_FOLDER_HELP,
} from './workspace'

function q(
  area: string,
  filename: string,
  id = 'id',
): WorkspaceQuoteRef {
  return { id, area, filename }
}

describe('WORKSPACE_FOLDER_HELP', () => {
  it('lists expected folders', () => {
    const folders = WORKSPACE_FOLDER_HELP.map((x) => x.folder)
    expect(folders).toContain('agents')
    expect(folders).toContain('inbox')
  })
})

describe('formatWorkspaceTargetBlocks', () => {
  it('returns empty for no quotes', () => {
    expect(formatWorkspaceTargetBlocks([])).toBe('')
  })

  it('formats blocks with trailing newlines', () => {
    const s = formatWorkspaceTargetBlocks([
      q('notes', 'a.md'),
      q('inbox', 'b.pdf'),
    ])
    expect(s).toContain('[workspace_target]')
    expect(s).toContain('area: notes')
    expect(s).toContain('filename: a.md')
    expect(s.endsWith('\n\n')).toBe(true)
  })
})

describe('isAgentsYamlRef', () => {
  it('matches agents yaml/yml', () => {
    expect(isAgentsYamlRef(q('agents', 'foo.yaml'))).toBe(true)
    expect(isAgentsYamlRef(q('agents', 'Foo.YML'))).toBe(true)
    expect(isAgentsYamlRef(q('agents', 'x.txt'))).toBe(false)
    expect(isAgentsYamlRef(q('notes', 'foo.yaml'))).toBe(false)
  })
})

describe('agentIdFromAgentsFilename', () => {
  it('strips extension and lowercases', () => {
    expect(agentIdFromAgentsFilename('MyAgent.yaml')).toBe('myagent')
    expect(agentIdFromAgentsFilename('X.YML')).toBe('x')
  })

  it('trims after replace so trailing spaces prevent stripping', () => {
    expect(agentIdFromAgentsFilename('  X.YML  ')).toBe('x.yml')
  })
})

describe('dedupeAgentIdsFromQuotes', () => {
  it('collects unique agent ids from yaml refs', () => {
    expect(
      dedupeAgentIdsFromQuotes([
        q('agents', 'a.yaml'),
        q('agents', 'a.yml'),
        q('agents', 'b.yaml'),
        q('notes', 'c.yaml'),
      ]),
    ).toEqual(['a', 'b'])
  })
})

describe('dedupeAgentYamlQuotesForDisplay', () => {
  it('keeps first quote per agent id', () => {
    const first = q('agents', 'dup.yaml', '1')
    const second = q('agents', 'Dup.YML', '2')
    const out = dedupeAgentYamlQuotesForDisplay([first, second])
    expect(out).toHaveLength(1)
    expect(out[0].id).toBe('1')
  })
})
