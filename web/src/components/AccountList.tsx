import type { Account } from '../types'

export function AccountList({
  accounts,
  selected,
  onSelect,
}: {
  accounts: Account[]
  selected: string
  onSelect: (id: string) => void
}) {
  return (
    <div className="panel">
      <div className="panel-title">Accounts</div>
      {accounts.map((a) => (
        <button
          key={a.id}
          className={`account ${a.id === selected ? 'active' : ''}`}
          onClick={() => onSelect(a.id)}
        >
          <div className="account-name">{a.name}</div>
          <div className="account-meta">
            ${a.arr?.toLocaleString()} · renews {a.renewal}
          </div>
        </button>
      ))}
      {!accounts.length && <div className="muted small">No accounts loaded.</div>}
    </div>
  )
}
