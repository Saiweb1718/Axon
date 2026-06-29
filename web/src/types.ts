export interface Health { ok: boolean; llm: string; embeddings: string; domain: string }
export interface Account { id: string; name: string; arr: number; renewal: string; signals?: number }
export interface AgentInfo { name: string; description: string; inputs: string[]; outputs: string[] }
export interface Evidence { source: string; ref: string; snippet: string; score: number }

export interface Finding {
  type: string
  description: string
  severity: string
  urgency: string
  confidence: number
  evidence?: string
}

export interface Reasoning {
  risks?: string[]
  opportunities?: string[]
  missing?: string[]
  findings?: Finding[]
}

export interface Recommendation {
  id: string
  account_id: string
  action: string
  rationale: string
  confidence: number
  factors: Record<string, number>
  score: number
  priority: string
  rank: number
  evidence: Evidence[]
  reasoning_trace: Reasoning
  down_ranked_by_feedback: boolean
  status: string
}

export interface Artifact {
  channel: string
  title: string
  recipient: string
  body: string
  due_in_days: number
}

export interface Delivery {
  channel: string
  created: boolean
  to?: string
  subject?: string
  reason?: string
}

export interface DecisionResponse {
  ok: boolean
  decision: string
  artifact?: Artifact
  delivery?: Delivery
}

export interface RecommendResult {
  account_id: string
  goal: string
  plan: string[]
  trace: string[]
  recommendations: Recommendation[]
}

export interface Feedback {
  recommendation_id: string
  account_id: string
  action: string
  decision: 'approved' | 'rejected' | 'edited'
  note?: string
  edited_action?: string
}

export interface Interaction {
  id: string
  account_id: string
  kind: string
  text: string
  ts: number
}

export interface DecisionRow {
  account_id: string
  action: string
  decision: string
  note: string
  ts: number
}

export interface AccountDetail {
  account: Account & { usage?: string }
  timeline: Interaction[]
  decisions: DecisionRow[]
}

export interface GraphNode { id: string; type: string; label: string }
export interface GraphEdge { source: string; target: string; rel: string }
export interface GraphData { nodes: GraphNode[]; edges: GraphEdge[] }

export interface SearchResult { query: string; results: Evidence[] }

export interface EvalRow {
  account: string
  expected: string[]
  top_action: string
  matched_rank: number
  top1: boolean
}

export interface EvalResult {
  n_cases: number
  top1_accuracy: number
  mrr: number
  learning_check: { account: string; rejected: string; new_top: string; changed_after_feedback: boolean } | null
  rows: EvalRow[]
  embeddings: string
  llm: string
}
