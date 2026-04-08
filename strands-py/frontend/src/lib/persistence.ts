import type { ChatMessage } from '../types/chat'
import type {
  ProjectPersist,
  UploadedRef,
  WorkspaceQuoteRef,
} from '../types/project'

export const LS_KEY = 'strands-py-app-v1'
const MAX_PROJECT_ID_LEN = 128
const PROJECT_ID_RE = /^[a-zA-Z0-9._-]+$/

export function isValidProjectId(id: string): boolean {
  return (
    id.length >= 1 &&
    id.length <= MAX_PROJECT_ID_LEN &&
    PROJECT_ID_RE.test(id)
  )
}

export function emptyProjectPersist(): ProjectPersist {
  return {
    messages: [],
    workspaceQuotes: [],
    agentId: '',
    mode: 'default',
    input: '',
    uploadedRefs: [],
    teamLandingOpen: false,
  }
}

export function parsePersisted(raw: string | null): {
  activeProjectId: string
  byProject: Record<string, ProjectPersist>
} {
  if (!raw) return { activeProjectId: 'default', byProject: {} }
  try {
    const p = JSON.parse(raw) as {
      activeProjectId?: unknown
      byProject?: Record<string, Partial<ProjectPersist>>
    }
    const byProject: Record<string, ProjectPersist> = {}
    if (p.byProject && typeof p.byProject === 'object') {
      for (const [k, v] of Object.entries(p.byProject)) {
        if (!isValidProjectId(k)) continue
        const mode =
          v.mode === 'skills' ||
          v.mode === 'workflow' ||
          v.mode === 'swarm' ||
          v.mode === 'default'
            ? v.mode
            : 'default'
        byProject[k] = {
          messages: Array.isArray(v.messages) ? (v.messages as ChatMessage[]) : [],
          workspaceQuotes: Array.isArray(v.workspaceQuotes)
            ? (v.workspaceQuotes as WorkspaceQuoteRef[])
            : [],
          agentId: typeof v.agentId === 'string' ? v.agentId : '',
          mode,
          input: typeof v.input === 'string' ? v.input : '',
          uploadedRefs: Array.isArray(v.uploadedRefs)
            ? (v.uploadedRefs as UploadedRef[])
            : [],
          teamLandingOpen: v.teamLandingOpen === true,
        }
      }
    }
    const aid =
      typeof p.activeProjectId === 'string' && isValidProjectId(p.activeProjectId)
        ? p.activeProjectId
        : 'default'
    return { activeProjectId: aid, byProject }
  } catch {
    return { activeProjectId: 'default', byProject: {} }
  }
}

export function readBootState(): {
  activeProjectId: string
  slice: ProjectPersist
  vault: Record<string, ProjectPersist>
} {
  try {
    const raw =
      typeof localStorage !== 'undefined' ? localStorage.getItem(LS_KEY) : null
    const p = parsePersisted(raw)
    const slice = p.byProject[p.activeProjectId] ?? emptyProjectPersist()
    return {
      activeProjectId: p.activeProjectId,
      slice,
      vault: { ...p.byProject, [p.activeProjectId]: slice },
    }
  } catch {
    const slice = emptyProjectPersist()
    return {
      activeProjectId: 'default',
      slice,
      vault: { default: { ...slice } },
    }
  }
}
