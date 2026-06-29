import { useEffect, useState } from 'react'
import * as api from './api'
import type { Account, AgentInfo, Health } from './types'
import { Header } from './components/Header'
import { PortfolioView } from './components/PortfolioView'
import { AccountView } from './components/AccountView'
import { MemoryView } from './components/MemoryView'
import { EvalView } from './components/EvalView'

type Tab = 'portfolio' | 'account' | 'memory' | 'eval'

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [tab, setTab] = useState<Tab>('portfolio')
  const [selected, setSelected] = useState('')
  const [toast, setToast] = useState('')
  const [error, setError] = useState('')

  function loadAccounts() {
    return api
      .getAccounts()
      .then(setAccounts)
      .catch(() =>
        setError('Cannot reach the backend on http://127.0.0.1:8000 — start it with:  uvicorn app.main:app --reload'),
      )
  }

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
    api.getAgents().then(setAgents).catch(() => {})
    loadAccounts()
  }, [])

  function flash(m: string) {
    setToast(m)
    window.setTimeout(() => setToast(''), 3600)
  }
  function openAccount(id: string) {
    setSelected(id)
    setTab('account')
  }

  const current = accounts.find((a) => a.id === selected) || accounts[0]
  const tabs: [Tab, string][] = [
    ['portfolio', 'Portfolio'],
    ['account', 'Account'],
    ['memory', 'Memory Explorer'],
    ['eval', 'Evaluation'],
  ]

  return (
    <div className="app">
      <Header health={health} />

      <nav className="tabs">
        {tabs.map(([t, label]) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {label}
          </button>
        ))}
      </nav>

      <div className="content">
        {error && <div className="banner error">{error}</div>}
        {tab === 'portfolio' && (
          <PortfolioView accounts={accounts} agents={agents} onOpen={openAccount} onChanged={loadAccounts} />
        )}
        {tab === 'account' &&
          (current ? (
            <AccountView account={current} accounts={accounts} onSelect={setSelected} onToast={flash} onChanged={loadAccounts} />
          ) : (
            <div className="empty">No accounts yet — add one in Portfolio.</div>
          ))}
        {tab === 'memory' && <MemoryView accounts={accounts} />}
        {tab === 'eval' && <EvalView />}
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
