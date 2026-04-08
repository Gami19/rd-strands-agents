import type { WorkspaceQuoteRef } from '../types/project'

export const WORKSPACE_FOLDER_HELP: { folder: string; description: string }[] = [
  {
    folder: 'inbox',
    description:
      '外部からの取り込みや一次置き場。PDF 変換ツールの出力先などにも',
  },
  {
    folder: 'notes',
    description: 'メモ・調査記録。検討中のたたき台やメモ置き場',
  },
  {
    folder: 'proposal',
    description: '提案資料やドラフト。図面の下書き（drawio 等）の置き場にも',
  },
  {
    folder: 'decision',
    description: '決定事項・ADR など、確定した記録',
  },
  {
    folder: 'agents',
    description: 'エージェント定義 YAML',
  },
]

export function formatWorkspaceTargetBlocks(quotes: WorkspaceQuoteRef[]): string {
  if (!quotes.length) return ''
  return (
    quotes
      .map(
        (q) =>
          `[workspace_target]\narea: ${q.area}\nfilename: ${q.filename}\n[/workspace_target]`,
      )
      .join('\n\n') + '\n\n'
  )
}

export function isAgentsYamlRef(q: WorkspaceQuoteRef): boolean {
  return q.area === 'agents' && /\.ya?ml$/i.test(q.filename)
}

export function agentIdFromAgentsFilename(filename: string): string {
  return filename.replace(/\.(yaml|yml)$/i, '').trim().toLowerCase()
}

export function dedupeAgentIdsFromQuotes(quotes: WorkspaceQuoteRef[]): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const q of quotes) {
    if (!isAgentsYamlRef(q)) continue
    const id = agentIdFromAgentsFilename(q.filename)
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(id)
  }
  return out
}

export function dedupeAgentYamlQuotesForDisplay(
  quotes: WorkspaceQuoteRef[],
): WorkspaceQuoteRef[] {
  const seen = new Set<string>()
  const out: WorkspaceQuoteRef[] = []
  for (const q of quotes) {
    if (!isAgentsYamlRef(q)) continue
    const id = agentIdFromAgentsFilename(q.filename)
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(q)
  }
  return out
}
