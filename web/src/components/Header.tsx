import type { Health } from '../types'

export function Header({ health }: { health: Health | null }) {
  return (
    <header className="header">
      <div className="brand">
        <span className="logo">◇</span>
        <div>
          <div className="title">Axon</div>
          <div className="subtitle">Intelligent Next Best Action Platform</div>
        </div>
      </div>
      <div className="status">
        {health ? (
          <>
            <span className="chip">domain: {health.domain}</span>
            <span className="chip">llm: {health.llm}</span>
            <span className="chip ok">● online</span>
          </>
        ) : (
          <span className="chip warn">● connecting…</span>
        )}
      </div>
    </header>
  )
}
