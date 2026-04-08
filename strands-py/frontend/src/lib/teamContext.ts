/**
 * team_context ID と表示ラベルは backend の
 * src/infrastructure/team_context.py（VALID_TEAM_CONTEXTS / team_context_labels）と同期すること。
 */

export type TeamContextId =
  | 'developer'
  | 'marketing'
  | 'hr'
  | 'pmo'
  | 'engineering'

export const TEAM_CONTEXT_OPTIONS: { id: TeamContextId; label: string }[] = [
  { id: 'developer', label: 'Developer' },
  { id: 'marketing', label: 'Marketing Teams' },
  { id: 'hr', label: 'HR Teams' },
  { id: 'pmo', label: 'PMO Teams' },
  { id: 'engineering', label: 'Engineering Teams' },
]

export function workflowEnabled(teamContext: string): boolean {
  return teamContext === 'developer'
}

const LS_ACK_TEAM_PR = 'strands_ack_team_pr_v1'

export function hasAcknowledgedTeamPrNotice(): boolean {
  try {
    return localStorage.getItem(LS_ACK_TEAM_PR) === '1'
  } catch {
    return false
  }
}

export function setAcknowledgedTeamPrNotice(): void {
  try {
    localStorage.setItem(LS_ACK_TEAM_PR, '1')
  } catch {
    /* ignore */
  }
}
