export type Role = 'user' | 'assistant' | 'handoff'

export type ToolTraceEntry = {
  name: string
  stream_revision?: number
  input?: unknown
}

export type WorkspaceTargetInMessage = {
  id: string
  area: string
  filename: string
}

export type ChatMessage = {
  id: string
  role: Role
  text: string
  reasoning?: string
  toolTrace?: ToolTraceEntry[]
  streamContext?: { phase?: string; agent?: string }
  fromAgents?: string[]
  toAgents?: string[]
  handoffMessage?: string
  multiAgentIds?: string[]
  selectedAgentId?: string
  workspaceTargets?: WorkspaceTargetInMessage[]
}

export type ChatMode = 'default' | 'skills' | 'workflow' | 'swarm'

export type StreamPayload =
  | { type: 'text'; content: string; phase?: string; agent?: string }
  | { type: 'reasoning'; content: string; phase?: string; agent?: string }
  | {
      type: 'tool'
      name: string
      input?: unknown
      stream_revision?: number
      error?: unknown
      status?: unknown
      phase?: string
      agent?: string
    }
  | {
      type: 'interrupt'
      session_id: string
      interrupts: {
        id: string
        name?: string | null
        reason?: unknown
      }[]
      phase?: string
      agent?: string
    }
  | {
      type: 'handoff'
      from_agents: string[]
      to_agents: string[]
      message?: string | null
      phase?: string
      agent?: string
    }
  | { type: 'done'; stop_reason: string | null; phase?: string; agent?: string }
  | {
      type: 'error'
      message: string
      code?: string
      phase?: string
      agent?: string
    }
