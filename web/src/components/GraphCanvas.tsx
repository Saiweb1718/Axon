import { useMemo } from 'react'
import type { GraphData } from '../types'

const COLORS: Record<string, string> = {
  account: '#ffffff', interaction: '#8f8f8f', risk: '#f85149', opportunity: '#3fb950',
  stakeholder: '#d29922', product: '#58a6ff', playbook: '#a371f7', decision: '#ec6547',
}
const RADIUS: Record<string, number> = {
  account: 9, playbook: 7, decision: 6, risk: 6, opportunity: 6, stakeholder: 6, product: 6, interaction: 4,
}

const W = 760

/** Tiny deterministic force layout (no dependencies) — repulsion + edge springs. */
function layout(data: GraphData, H: number) {
  const { nodes, edges } = data
  const p = new Map(nodes.map((n, i) => {
    const a = i * 2.399963 // golden angle -> even initial spread (deterministic)
    return [n.id, { x: W / 2 + Math.cos(a) * 150, y: H / 2 + Math.sin(a) * 130, vx: 0, vy: 0 }]
  }))
  for (let it = 0; it < 150; it++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let k = i + 1; k < nodes.length; k++) {
        const a = p.get(nodes[i].id)!, b = p.get(nodes[k].id)!
        let dx = a.x - b.x, dy = a.y - b.y
        const d2 = dx * dx + dy * dy + 0.01, d = Math.sqrt(d2), f = 1700 / d2
        dx /= d; dy /= d
        a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f
      }
    }
    for (const e of edges) {
      const a = p.get(e.source), b = p.get(e.target)
      if (!a || !b) continue
      let dx = b.x - a.x, dy = b.y - a.y
      const d = Math.sqrt(dx * dx + dy * dy) + 0.01, f = (d - 64) * 0.02
      dx /= d; dy /= d
      a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f
    }
    for (const n of nodes) {
      const q = p.get(n.id)!
      q.vx += (W / 2 - q.x) * 0.004; q.vy += (H / 2 - q.y) * 0.004
      q.x += Math.max(-6, Math.min(6, q.vx)); q.y += Math.max(-6, Math.min(6, q.vy))
      q.vx *= 0.86; q.vy *= 0.86
    }
  }
  return p
}

export function GraphCanvas({ data, height = 440 }: { data: GraphData; height?: number }) {
  const pos = useMemo(() => layout(data, height), [data, height])
  if (!data.nodes.length)
    return <div className="empty">No memory yet — ingest interactions to build the graph.</div>

  const types = Array.from(new Set(data.nodes.map((n) => n.type)))
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${height}`} className="graph" role="img" aria-label="knowledge graph">
        {data.edges.map((e, i) => {
          const a = pos.get(e.source), b = pos.get(e.target)
          if (!a || !b) return null
          return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#262626" strokeWidth={1} />
        })}
        {data.nodes.map((n) => {
          const q = pos.get(n.id)!
          const color = COLORS[n.type] || '#8f8f8f'
          return (
            <g key={n.id}>
              <circle cx={q.x} cy={q.y} r={RADIUS[n.type] || 5} fill={color} stroke="#0d0d0d" strokeWidth={1}>
                <title>{n.type}: {n.label}</title>
              </circle>
              {(n.type === 'account' || n.type === 'playbook') && (
                <text x={q.x + 10} y={q.y + 3} className="glabel">{n.label.slice(0, 22)}</text>
              )}
            </g>
          )
        })}
      </svg>
      <div className="legend">
        {types.map((t) => (
          <span key={t} className="leg"><i style={{ background: COLORS[t] || '#8f8f8f' }} />{t}</span>
        ))}
      </div>
    </div>
  )
}
