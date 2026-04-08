import type { ChatMessage, ChatMode } from './chat'

export type UploadedRef = {
  id: string
  kind: 'pdf' | 'markdown' | 'image' | 'file'
  url: string
  filename: string
}

export type ArtifactItem = {
  folder: string
  filename: string
  url: string
  size: number
  modified: string
}

export type WorkspaceQuoteRef = {
  id: string
  area: string
  filename: string
}

export type ProjectPersist = {
  messages: ChatMessage[]
  workspaceQuotes: WorkspaceQuoteRef[]
  agentId: string
  mode: ChatMode
  input: string
  uploadedRefs: UploadedRef[]
  teamLandingOpen: boolean
}

export type ProjectListEntry = {
  project_id: string
  display_name: string
  team_context?: string
  team_context_label?: string
  meta_error?: boolean
  detail?: string
}

export type AgentListItem = {
  agent_id: string
  name: string
  kind?: 'single' | 'orchestrator' | 'swarm'
  description?: string
  department?: string | null
  division?: string | null
  icon_key?: string | null
}
