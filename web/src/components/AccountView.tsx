import { useEffect, useState } from 'react'
import * as api from '../api'
import type { Account, AccountDetail, Recommendation, RecommendResult } from '../types'
import { RecommendationCard } from './RecommendationCard'
import { TracePanel } from './TracePanel'

const KINDS = ['meeting_note', 'email', 'ticket', 'crm_update', 'usage', 'note']

export function AccountView({ account, accounts, onSelect, onToast, onChanged }: {
  account: Account
  accounts: Account[]
  onSelect: (id: string) => void
  onToast: (m: string) => void
  onChanged: () => void
}) {
  const [detail, setDetail] = useState<AccountDetail | null>(null)
  const [result, setResult] = useState<RecommendResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [text, setText] = useState('')
  const [kind, setKind] = useState('meeting_note')

  function load() { api.getAccount(account.id).then(setDetail).catch(() => {}) }
  useEffect(() => { setResult(null); load() }, [account.id])

  async function run() {
    setLoading(true)
    try { setResult(await api.recommend(account.id)) } finally { setLoading(false) }
  }
  async function addSignal() {
    if (!text.trim()) return
    await api.ingest(account.id, [{ kind, text }])
    setText(''); load(); onChanged(); onToast('Signal ingested into memory.')
  }
  async function onApprove(r: Recommendation) {
    const res = await api.decide({ recommendation_id: r.id, account_id: r.account_id, action: r.action, decision: 'approved' })
    const gmail = res.delivery?.created ? ' → Gmail draft created' : ''
    onToast(`Approved — drafted a ${res.artifact?.channel ?? 'next step'}${gmail}`)
    return res
  }
  async function onReject(r: Recommendation) {
    await api.decide({ recommendation_id: r.id, account_id: r.account_id, action: r.action, decision: 'rejected', note: 'Rejected by reviewer' })
    onToast('Rejected — re-running so you can watch it learn…'); await run(); load()
  }
  async function onEdit(r: Recommendation) {
    const edited = window.prompt('Edit the recommended action:', r.action)
    if (!edited || edited === r.action) return
    await api.decide({ recommendation_id: r.id, account_id: r.account_id, action: r.action, decision: 'edited', edited_action: edited })
    onToast('Saved your edit.')
  }

  return (
    <div>
      <div className="subtabs">
        {accounts.map((a) => (
          <button key={a.id} className={`subtab ${a.id === account.id ? 'active' : ''}`} onClick={() => onSelect(a.id)}>{a.name}</button>
        ))}
      </div>

      <div className="account-grid">
        <div>
          <div className="run-bar">
            <div>
              <h2>{account.name}</h2>
              <p className="muted small tnum">
                ARR ${account.arr?.toLocaleString()} · renewal {account.renewal}
                {detail?.account.usage ? ` · usage: ${detail.account.usage}` : ''}
              </p>
            </div>
            <button className="btn primary" disabled={loading} onClick={run}>{loading ? 'Thinking…' : 'Run next best actions'}</button>
          </div>

          {loading && (
            <div className="cards">
              {[0, 1].map((i) => (
                <div className="card skeleton-card" key={i}>
                  <div className="sk sk-line w60" /><div className="sk sk-bar" /><div className="sk sk-line w90" />
                </div>
              ))}
            </div>
          )}

          {!loading && result && (
            <>
              <div className="plan">
                <span className="muted small">PLAN</span>
                {result.plan.map((p, i) => (
                  <span key={i} className="pill">{p}{i < result.plan.length - 1 ? <span className="arrow"> → </span> : null}</span>
                ))}
              </div>
              <div className="cards">
                {result.recommendations.map((r, i) => (
                  <RecommendationCard key={r.id} rec={r} index={i} onApprove={onApprove} onReject={onReject} onEdit={onEdit} />
                ))}
              </div>
              <TracePanel trace={result.trace} />
            </>
          )}

          {!loading && !result && (
            <div className="empty">
              Run the planner for next best actions — or ingest a new signal on the right and re-run to watch memory change the result.
            </div>
          )}
        </div>

        <aside className="timeline-col">
          <div className="panel">
            <div className="panel-title">Ingest interaction</div>
            <select className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
              {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
            <textarea className="input" placeholder="Paste a note, email, ticket…" value={text} onChange={(e) => setText(e.target.value)} />
            <button className="btn" onClick={addSignal} disabled={!text.trim()}>Remember</button>
          </div>

          <div className="panel">
            <div className="panel-title">Timeline ({detail?.timeline.length ?? 0})</div>
            {detail?.timeline.map((i) => (
              <div className="tl" key={i.id}><span className="tl-kind">{i.kind}</span><span className="tl-text">{i.text}</span></div>
            ))}
            {detail?.decisions?.length ? <div className="panel-title" style={{ marginTop: 14 }}>Decisions ({detail.decisions.length})</div> : null}
            {detail?.decisions?.map((d, i) => (
              <div className="tl" key={i}>
                <span className={`tl-kind ${d.decision === 'rejected' ? 'rej' : 'app'}`}>{d.decision}</span>
                <span className="tl-text">{d.action}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  )
}
