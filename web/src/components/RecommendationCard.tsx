import { useState, type CSSProperties } from 'react'
import type { Artifact, DecisionResponse, Delivery, Recommendation } from '../types'

const PRIO: Record<string, string> = { HIGH: 'green', MEDIUM: 'amber', LOW: 'muted' }
const FACTORS = ['impact', 'urgency', 'confidence', 'effort'] as const

export function RecommendationCard({
  rec,
  index,
  onApprove,
  onReject,
  onEdit,
}: {
  rec: Recommendation
  index: number
  onApprove: (r: Recommendation) => Promise<DecisionResponse | undefined> | void
  onReject: (r: Recommendation) => void
  onEdit: (r: Recommendation) => void
}) {
  const [open, setOpen] = useState(false)
  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [delivery, setDelivery] = useState<Delivery | null>(null)
  const [approving, setApproving] = useState(false)
  const risks = rec.reasoning_trace?.risks ?? []
  const opps = rec.reasoning_trace?.opportunities ?? []
  const findings = rec.reasoning_trace?.findings ?? []
  const tone = PRIO[rec.priority] ?? 'amber'
  const score = Math.round((rec.score ?? rec.confidence) * 100)

  async function approve() {
    setApproving(true)
    try {
      const res = await onApprove(rec)
      if (res?.artifact) setArtifact(res.artifact)
      if (res?.delivery) setDelivery(res.delivery)
    } finally {
      setApproving(false)
    }
  }

  return (
    <div className={`card ${rec.down_ranked_by_feedback ? 'demoted' : ''}`} style={{ ['--i']: index } as CSSProperties}>
      <div className="card-head">
        <span className="rank">#{rec.rank}</span>
        <div className="action">{rec.action}</div>
        <span className={`prio ${tone}`}>{rec.priority}</span>
        {rec.down_ranked_by_feedback && <span className="badge learned">↓ learned</span>}
      </div>

      <div className="confidence">
        <div className="bar">
          <div className={`fill ${tone}`} style={{ width: `${score}%` }} />
        </div>
        <span className={`conf-val ${tone}`}>{score}</span>
        <span className="conf-tag muted">priority score</span>
      </div>

      <div className="factors">
        {FACTORS.map((f) => (
          <div className="factor" key={f}>
            <span className="factor-label">{f}</span>
            <div className="factor-bar">
              <div className="factor-fill" style={{ width: `${Math.round((rec.factors?.[f] ?? 0) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>

      <p className="rationale">{rec.rationale}</p>

      <button className="link" onClick={() => setOpen(!open)}>
        {open ? 'Hide' : 'Show'} evidence & reasoning
      </button>
      {open && (
        <div className="evidence">
          {findings.length > 0 ? (
            <div className="finding-list">
              {findings.map((f, i) => (
                <div className="finding" key={i}>
                  <span className={`ftype ${f.type}`}>{f.type}</span>
                  <span className="fmeta">sev {f.severity} · urg {f.urgency} · {Math.round((f.confidence ?? 0) * 100)}%</span>
                  <div className="fdesc">{f.description}</div>
                </div>
              ))}
            </div>
          ) : (
            <>
              {risks.length > 0 && (
                <div className="reason"><b>Risks:</b> {risks.join('; ')}</div>
              )}
              {opps.length > 0 && (
                <div className="reason"><b>Opportunities:</b> {opps.join('; ')}</div>
              )}
            </>
          )}
          <div className="ev-list">
            {rec.evidence.map((e, i) => (
              <div key={i} className="ev">
                <span className="ev-src">{e.source}</span> {e.snippet}
              </div>
            ))}
          </div>
        </div>
      )}

      {artifact && (
        <div className="artifact">
          <div className="artifact-head">
            <span className={`chan ${artifact.channel}`}>{artifact.channel}</span>
            <b>{artifact.title}</b>
          </div>
          <div className="artifact-meta">
            To: {artifact.recipient} · due in {artifact.due_in_days}d
          </div>
          <pre className="artifact-body">{artifact.body}</pre>
          {delivery && (
            <div className={`delivery ${delivery.created ? 'ok' : 'pending'}`}>
              {delivery.created
                ? `✓ Draft created in your Gmail${delivery.to ? ` — to ${delivery.to}` : ''}`
                : `Draft shown above (not pushed) — ${delivery.reason ?? 'Gmail not configured'}`}
            </div>
          )}
        </div>
      )}

      <div className="actions">
        <button className="btn approve" onClick={approve} disabled={approving || !!artifact}>
          {approving ? 'Drafting…' : artifact ? 'Approved ✓' : 'Approve'}
        </button>
        <button className="btn edit" onClick={() => onEdit(rec)}>
          Edit
        </button>
        <button className="btn reject" onClick={() => onReject(rec)}>
          Reject
        </button>
      </div>
    </div>
  )
}
