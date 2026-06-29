import { useState } from 'react'
import * as api from '../api'
import type { Account, AgentInfo } from '../types'
import { AgentCatalog } from './AgentCatalog'

const TODAY = new Date('2026-06-27')

export function PortfolioView({ accounts, agents, onOpen, onChanged }: {
  accounts: Account[]; agents: AgentInfo[]; onOpen: (id: string) => void; onChanged: () => void
}) {
  const totalArr = accounts.reduce((s, a) => s + (a.arr || 0), 0)
  const soon = accounts.filter((a) => {
    const d = a.renewal ? (new Date(a.renewal).getTime() - TODAY.getTime()) / 86_400_000 : Infinity
    return d >= 0 && d <= 90
  }).length

  const [open, setOpen] = useState(false)
  const [name, setName] = useState(''); const [arr, setArr] = useState('')
  const [renewal, setRenewal] = useState(''); const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  const kpis = [
    { label: 'Accounts', value: String(accounts.length), sub: 'in portfolio' },
    { label: 'Portfolio ARR', value: '$' + Math.round(totalArr / 1000) + 'k', sub: 'annual recurring' },
    { label: 'Renewing ≤90d', value: String(soon), sub: soon ? 'need attention' : 'all clear', tone: soon ? 'amber' : 'green' },
    { label: 'Agents', value: String(agents.length), sub: 'planner-orchestrated' },
  ]

  async function add() {
    if (!name) return
    setBusy(true)
    try {
      await api.createAccount({
        name, arr: Number(arr) || 0, renewal, usage: 'stable',
        interactions: note ? [{ kind: 'note', text: note }] : [],
      })
      setName(''); setArr(''); setRenewal(''); setNote(''); setOpen(false)
      onChanged()
    } finally { setBusy(false) }
  }

  return (
    <div>
      <div className="kpis">
        {kpis.map((k) => (
          <div className="kpi" key={k.label}>
            <div className="kpi-label">{k.label}</div>
            <div className={`kpi-value ${k.tone ?? ''}`}>{k.value}</div>
            <div className="kpi-sub">{k.sub}</div>
          </div>
        ))}
      </div>

      <div className="run-bar">
        <h2>Portfolio</h2>
        <button className="btn primary" onClick={() => setOpen(!open)}>{open ? 'Cancel' : '+ Add customer'}</button>
      </div>

      {open && (
        <div className="form-card">
          <div className="form-row">
            <input className="input" placeholder="Company name" value={name} onChange={(e) => setName(e.target.value)} />
            <input className="input" placeholder="ARR e.g. 90000" value={arr} onChange={(e) => setArr(e.target.value)} />
            <input className="input" placeholder="Renewal YYYY-MM-DD" value={renewal} onChange={(e) => setRenewal(e.target.value)} />
          </div>
          <textarea className="input" placeholder="First interaction — a meeting note, email, or signal…" value={note} onChange={(e) => setNote(e.target.value)} />
          <button className="btn primary" disabled={busy || !name} onClick={add}>{busy ? 'Adding…' : 'Create customer'}</button>
        </div>
      )}

      <table className="table">
        <thead><tr><th>Account</th><th>ARR</th><th>Renewal</th><th>Signals</th><th /></tr></thead>
        <tbody>
          {accounts.map((a) => (
            <tr key={a.id}>
              <td className="td-name">{a.name}</td>
              <td className="tnum">${a.arr?.toLocaleString()}</td>
              <td className="tnum">{a.renewal}</td>
              <td className="tnum">{a.signals ?? '—'}</td>
              <td><button className="btn small-btn" onClick={() => onOpen(a.id)}>Open →</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 22 }}><AgentCatalog agents={agents} /></div>
    </div>
  )
}
