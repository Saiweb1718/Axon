import type { AgentInfo } from '../types'

export function AgentCatalog({ agents }: { agents: AgentInfo[] }) {
  return (
    <div className="panel">
      <div className="panel-title">
        Agent registry <span className="muted small">({agents.length})</span>
      </div>
      {agents.map((a) => (
        <div key={a.name} className="agent">
          <div className="agent-name">{a.name}</div>
          <div className="agent-desc">{a.description}</div>
        </div>
      ))}
      <div className="muted small hint">
        Drop a new agent in <code>app/agents/</code> and it appears here — the planner picks it up automatically.
      </div>
    </div>
  )
}
