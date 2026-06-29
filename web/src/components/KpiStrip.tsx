import type { Account, RecommendResult } from '../types'

const TODAY = new Date('2026-06-26')

function money(n: number): string {
  if (n >= 1000) return '$' + Math.round(n / 1000) + 'k'
  return '$' + n
}

function daysUntil(dateStr: string): number {
  return (new Date(dateStr).getTime() - TODAY.getTime()) / 86_400_000
}

export function KpiStrip({ accounts, result }: { accounts: Account[]; result: RecommendResult | null }) {
  const totalArr = accounts.reduce((sum, a) => sum + (a.arr || 0), 0)
  const renewingSoon = accounts.filter((a) => {
    const d = a.renewal ? daysUntil(a.renewal) : Infinity
    return d >= 0 && d <= 90
  }).length

  const top = result?.recommendations?.[0]
  const topTone = top ? (top.confidence >= 0.75 ? 'green' : top.confidence >= 0.5 ? 'amber' : 'red') : ''

  const kpis: { label: string; value: string; sub: string; tone?: string }[] = [
    { label: 'Accounts', value: String(accounts.length), sub: 'in portfolio' },
    { label: 'Portfolio ARR', value: money(totalArr), sub: 'annual recurring' },
    {
      label: 'Renewing ≤90d',
      value: String(renewingSoon),
      sub: renewingSoon ? 'need attention' : 'all clear',
      tone: renewingSoon ? 'amber' : 'green',
    },
    {
      label: 'Top action',
      value: top ? Math.round(top.confidence * 100) + '%' : '—',
      sub: top ? 'confidence' : 'run to compute',
      tone: topTone,
    },
  ]

  return (
    <div className="kpis">
      {kpis.map((k) => (
        <div className="kpi" key={k.label}>
          <div className="kpi-label">{k.label}</div>
          <div className={`kpi-value ${k.tone ?? ''}`}>{k.value}</div>
          <div className="kpi-sub">{k.sub}</div>
        </div>
      ))}
    </div>
  )
}
