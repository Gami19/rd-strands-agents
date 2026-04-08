import type { TeamContextId } from '../lib/teamContext'
import type { AgentListItem } from '../types/project'

type TeamCopy = {
  title: string
  description: string
}

const TEAM_COPY: Record<TeamContextId, TeamCopy> = {
  developer: {
    title: 'Developer',
    description: 'このチームでは説明ビューは利用しません。',
  },
  marketing: {
    title: 'Marketing Teams',
    description:
      'PR・採用広報・SNS・調査分析・事例コンテンツを支援します。',
  },
  hr: {
    title: 'HR Teams',
    description:
      '採用、オンボーディング、成長支援、エンゲージメント、品質レビューを支援します。',
  },
  pmo: {
    title: 'PMO Teams',
    description:
      '提案・要件整理・図解・設計レビュー・運用計画など、プロジェクト推進に必要なドキュメント作成を支援します。',
  },
  engineering: {
    title: 'Engineering Teams',
    description:
      'アーキテクチャ、実装、テスト、可観測性、運用改善を支援します。',
  },
}

export type TeamLandingViewProps = {
  teamContext: TeamContextId
  agents: AgentListItem[]
  agentsLoading: boolean
  agentsError: string | null
  onStartChat: () => void
  onRequestAgent: (agentId: string) => void
}

type DivisionGroup = { label: string; items: AgentListItem[] }
type DepartmentGroup = { label: string; divisions: DivisionGroup[] }

function groupAgents(agents: AgentListItem[]): DepartmentGroup[] {
  const depMap = new Map<string, Map<string, AgentListItem[]>>()
  for (const a of agents) {
    const dep =
      typeof a.department === 'string' && a.department.trim()
        ? a.department.trim()
        : '未分類'
    const div =
      typeof a.division === 'string' && a.division.trim()
        ? a.division.trim()
        : 'メンバー'

    const divMap = depMap.get(dep) ?? new Map<string, AgentListItem[]>()
    const list = divMap.get(div) ?? []
    list.push(a)
    divMap.set(div, list)
    depMap.set(dep, divMap)
  }

  return Array.from(depMap.entries())
    .sort(([a], [b]) => a.localeCompare(b, 'ja'))
    .map(([depLabel, divMap]) => ({
      label: depLabel,
      divisions: Array.from(divMap.entries())
        .sort(([a], [b]) => a.localeCompare(b, 'ja'))
        .map(([divLabel, items]) => ({
          label: divLabel,
          items: items.sort((x, y) => x.name.localeCompare(y.name, 'ja')),
        })),
    }))
}

export function TeamLandingView({
  teamContext,
  agents,
  agentsLoading,
  agentsError,
  onStartChat,
  onRequestAgent,
}: TeamLandingViewProps) {
  const copy = TEAM_COPY[teamContext]
  const groups = groupAgents(agents)
  return (
    <section className="team-landing" aria-labelledby="team-landing-title">
      <h1 id="team-landing-title" className="team-landing-title">
        {copy.title}
      </h1>
      <p className="team-landing-description">{copy.description}</p>
      <div className="team-landing-actions">
        <button
          type="button"
          className="composer-send"
          onClick={onStartChat}
        >
          チャットを開始
        </button>
      </div>
      <div className="team-landing-select">
        <h2 className="team-landing-select-title">部門とエージェントを選択</h2>
        {agentsLoading ? (
          <p className="team-landing-muted">読み込み中…</p>
        ) : agentsError ? (
          <p className="team-landing-muted" role="alert">
            {agentsError}
          </p>
        ) : groups.length === 0 ? (
          <p className="team-landing-muted">
            エージェントが見つかりません。workspace の agents を確認してください。
          </p>
        ) : (
          <div className="team-dept-groups">
            {groups.map((dep) => (
              <section key={dep.label} className="team-dept-group">
                <h3 className="team-dept-group-title">{dep.label}</h3>
                <div className="team-division-grid">
                  {dep.divisions.map((div) => (
                    <section key={`${dep.label}-${div.label}`} className="team-division-group">
                      <h4 className="team-division-group-title">{div.label}</h4>
                      <ul className="team-dept-agent-list">
                        {div.items.map((a) => (
                          <li key={a.agent_id} className="team-dept-agent-item">
                            <div className="team-dept-agent-main">
                              <div className="team-dept-agent-name">{a.name}</div>
                              {a.description ? (
                                <p className="team-dept-agent-desc">{a.description}</p>
                              ) : null}
                            </div>
                            <button
                              type="button"
                              className="team-request-btn"
                              onClick={() => onRequestAgent(a.agent_id)}
                            >
                              依頼する
                            </button>
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
