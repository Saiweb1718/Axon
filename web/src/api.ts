import type {
  Account, AccountDetail, AgentInfo, DecisionResponse, EvalResult, Feedback, GraphData, Health, RecommendResult, SearchResult,
} from './types'

const BASE = (import.meta as { env?: { VITE_API?: string } }).env?.VITE_API ?? 'http://127.0.0.1:8000'

async function j<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...opts })
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return (await r.json()) as T
}

const post = (path: string, body: unknown) => ({ method: 'POST', body: JSON.stringify(body) })

export const getHealth = () => j<Health>('/health')
export const getAccounts = () => j<Account[]>('/accounts')
export const getAgents = () => j<AgentInfo[]>('/agents')

export const recommend = (account_id: string, goal?: string) =>
  j<RecommendResult>('/recommend', post('/recommend', goal ? { account_id, goal } : { account_id }))

export const decide = (fb: Feedback) => j<DecisionResponse>('/decision', post('/decision', fb))

export const createAccount = (body: {
  name: string; arr?: number; renewal?: string; usage?: string; interactions?: { kind: string; text: string }[]
}) => j<{ id: string; created: boolean; signals: number }>('/accounts', post('/accounts', body))

export const getAccount = (id: string) => j<AccountDetail>(`/accounts/${id}`)
export const getAccountMemory = (id: string) =>
  j<{ graph: GraphData; timeline: AccountDetail['timeline'] }>(`/accounts/${id}/memory`)
export const getMemoryGraph = (accountId?: string) =>
  j<GraphData>(`/memory/graph${accountId ? `?account_id=${accountId}` : ''}`)
export const memorySearch = (query: string, account_id?: string, k = 6) =>
  j<SearchResult>('/memory/search', post('/memory/search', { query, account_id, k }))
export const ingest = (account_id: string, interactions: { kind: string; text: string }[]) =>
  j<{ stored: number; account_id: string }>('/ingest', post('/ingest', { account_id, interactions }))
export const getEval = () => j<EvalResult>('/eval')
