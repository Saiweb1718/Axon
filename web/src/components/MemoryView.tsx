import { useEffect, useState } from 'react'
import * as api from '../api'
import type { Account, Evidence, GraphData } from '../types'
import { GraphCanvas } from './GraphCanvas'

export function MemoryView({ accounts }: { accounts: Account[] }) {
  const [scope, setScope] = useState('')
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] })
  const [query, setQuery] = useState('account at risk of churn before renewal')
  const [results, setResults] = useState<Evidence[]>([])
  const [searched, setSearched] = useState(false)

  useEffect(() => { api.getMemoryGraph(scope || undefined).then(setGraph).catch(() => {}) }, [scope])

  async function search() {
    const r = await api.memorySearch(query, scope || undefined, 6)
    setResults(r.results); setSearched(true)
  }

  return (
    <div>
      <div className="run-bar">
        <div>
          <h2>Memory Explorer</h2>
          <p className="muted small">The platform's shared memory — a knowledge graph + semantic vector recall.</p>
        </div>
        <select className="input scope" value={scope} onChange={(e) => setScope(e.target.value)}>
          <option value="">Whole organization</option>
          {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
      </div>

      <div className="memory-grid">
        <div className="panel">
          <div className="panel-title">Knowledge graph — {graph.nodes.length} nodes · {graph.edges.length} edges</div>
          <GraphCanvas data={graph} />
        </div>

        <div className="panel">
          <div className="panel-title">Semantic recall (vector + graph expansion)</div>
          <textarea className="input" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="btn primary" onClick={search}>Search memory</button>
          <div className="results">
            {searched && !results.length && <div className="muted small">No matches.</div>}
            {results.map((e, i) => (
              <div className="result" key={i}>
                <div className="result-head">
                  <span className="ev-src">{e.source}</span>
                  <span className="score tnum">{e.score.toFixed(2)}</span>
                </div>
                <div className="result-snip">{e.snippet}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
