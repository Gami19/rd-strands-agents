import { describe, expect, it } from 'vitest'
import { artifactFilePathUrl, ARTIFACT_FOLDERS } from './artifacts'

describe('ARTIFACT_FOLDERS', () => {
  it('has stable folder list', () => {
    expect(ARTIFACT_FOLDERS).toEqual([
      'agents',
      'decision',
      'inbox',
      'notes',
      'proposal',
    ])
  })
})

describe('artifactFilePathUrl', () => {
  it('builds path with encoded filename', () => {
    expect(artifactFilePathUrl('p1', 'notes', 'a b.md')).toBe(
      '/api/files/p1/notes/a%20b.md',
    )
  })
})
