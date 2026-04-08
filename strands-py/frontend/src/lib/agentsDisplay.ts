import type { AgentListItem, WorkspaceQuoteRef } from '../types/project'
import {
  agentIdFromAgentsFilename,
  isAgentsYamlRef,
} from './workspace'

export function agentDisplayNameForId(
  agentId: string,
  agents: AgentListItem[],
): string {
  const hit = agents.find((a) => a.agent_id === agentId)
  const n = hit?.name?.trim()
  return n || agentId
}

export function agentYamlDisplayName(
  filename: string,
  agents: AgentListItem[],
): string {
  if (!/\.ya?ml$/i.test(filename)) return filename
  const id = agentIdFromAgentsFilename(filename)
  const hit = agents.find((a) => a.agent_id === id)
  const n = hit?.name?.trim()
  return n || filename
}

export function workspaceQuoteChipLabel(
  q: WorkspaceQuoteRef,
  agents: AgentListItem[],
): string {
  if (isAgentsYamlRef(q)) return agentYamlDisplayName(q.filename, agents)
  return q.filename
}
