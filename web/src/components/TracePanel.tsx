import { useState } from 'react'

export function TracePanel({ trace }: { trace: string[] }) {
  const [open, setOpen] = useState(true)
  return (
    <div className="trace">
      <button className="trace-toggle" onClick={() => setOpen(!open)}>
        {open ? '▾' : '▸'} Planner reasoning trace ({trace.length} steps)
      </button>
      {open && (
        <ol className="trace-list">
          {trace.map((t, i) => (
            <li key={i}>{t}</li>
          ))}
        </ol>
      )}
    </div>
  )
}
