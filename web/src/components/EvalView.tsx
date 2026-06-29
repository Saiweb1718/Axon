import { useState } from 'react'
import * as api from '../api'
import type { EvalResult } from '../types'

export function EvalView() {
  const [data, setData] = useState<EvalResult | null>(null)
  const [loading, setLoading] = useState(false)

  async function run() {
    setLoading(true)
    try { setData(await api.getEval()) } finally { setLoading(false) }
  }

  return (
    <div>
      <div className="run-bar">
        <div>
          <h2>Evaluation</h2>
          <p className="muted small">Replays labelled accounts through the full platform and measures quality + that it learns. Reproducible (offline, clean store).</p>
        </div>
        <button className="btn primary" onClick={run} disabled={loading}>{loading ? 'Running…' : 'Run evaluation'}</button>
      </div>

      {!data && <div className="empty">Click “Run evaluation” to measure top-1 accuracy, MRR, and the before/after learning check.</div>}

      {data && (
        <>
          <div className="kpis">
            <div className="kpi"><div className="kpi-label">Top-1 accuracy</div><div className="kpi-value green">{Math.round(data.top1_accuracy * 100)}%</div><div className="kpi-sub">{data.n_cases} labelled cases</div></div>
            <div className="kpi"><div className="kpi-label">MRR</div><div className="kpi-value">{data.mrr.toFixed(2)}</div><div className="kpi-sub">mean reciprocal rank</div></div>
            <div className="kpi"><div className="kpi-label">Learns from feedback</div><div className={`kpi-value ${data.learning_check?.changed_after_feedback ? 'green' : 'red'}`}>{data.learning_check?.changed_after_feedback ? 'Yes' : 'No'}</div><div className="kpi-sub">top changed after a rejection</div></div>
            <div className="kpi"><div className="kpi-label">Stack</div><div className="kpi-value" style={{ fontSize: 15 }}>{data.embeddings}</div><div className="kpi-sub">llm: {data.llm}</div></div>
          </div>

          {data.learning_check && (
            <div className="form-card">
              <div className="panel-title">Learning check — {data.learning_check.account}</div>
              <div className="muted small">Rejected: <b style={{ color: 'var(--text)' }}>{data.learning_check.rejected}</b></div>
              <div className="muted small">New top after learning: <b style={{ color: 'var(--green)' }}>{data.learning_check.new_top}</b></div>
            </div>
          )}

          <table className="table">
            <thead><tr><th>Account</th><th>Top recommendation</th><th>Expected</th><th>Rank</th><th>✓</th></tr></thead>
            <tbody>
              {data.rows.map((r, i) => (
                <tr key={i}>
                  <td className="td-name">{r.account}</td>
                  <td>{r.top_action}</td>
                  <td className="muted small">{r.expected.join(', ')}</td>
                  <td className="tnum">{r.matched_rank || '—'}</td>
                  <td>{r.top1 ? '✓' : '·'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
