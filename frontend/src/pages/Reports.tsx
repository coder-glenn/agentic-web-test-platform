import React, { useEffect, useState } from 'react'

const AGENT_API = import.meta.env.VITE_AGENT_API || 'http://localhost:8000'

export default function Reports() {
  const [metrics, setMetrics] = useState<any>(null)
  const [summary, setSummary] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchReport()
  }, [])

  async function fetchReport() {
    setLoading(true)
    try {
      const res = await fetch(`${AGENT_API}/report`)
      const data = await res.json()
      setMetrics(data.metrics)
      setSummary(data.summary)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading report...</div>
  if (!metrics) return <div>No report available yet.</div>

  const successRate = metrics.total_tasks ? ((metrics.completed / Math.max(1, metrics.total_tasks)) * 100).toFixed(1) : 'N/A'

  return (
    <div style={{maxWidth:1000, margin:'20px auto', fontFamily:'Arial'}}>
      <h2>Test Report</h2>
      <div style={{display:'flex', gap:20}}>
        <div style={{flex:1, padding:12, border:'1px solid #ddd'}}>
          <h3>Key Metrics</h3>
          <p>Total tasks: {metrics.total_tasks}</p>
          <p>Completed: {metrics.completed}</p>
          <p>Failed: {metrics.failed}</p>
          <p>Pending: {metrics.pending}</p>
          <p>Success Rate: {successRate}%</p>
          <p>Avg Duration: {metrics.avg_duration_seconds ? metrics.avg_duration_seconds.toFixed(1) + 's' : 'N/A'}</p>
        </div>
        <div style={{flex:2, padding:12, border:'1px solid #ddd'}}>
          <h3>Failure Distribution</h3>
          {Object.keys(metrics.failure_distribution || {}).length === 0 && <div>No failures recorded.</div>}
          <ul>
            {Object.entries(metrics.failure_distribution || {}).map(([k,v]) => (
              <li key={k}>{k}: {v}</li>
            ))}
          </ul>
        </div>
      </div>

      <div style={{marginTop:20, padding:12, border:'1px solid #ddd'}}>
        <h3>AI Summary</h3>
        <p>{summary}</p>
      </div>

      <div style={{marginTop:20}}>
        <h3>Recent Tasks</h3>
        <pre style={{background:'#f6f6f6', padding:12, maxHeight:300, overflow:'auto'}}>{JSON.stringify(metrics.recent_tasks, null, 2)}</pre>
      </div>
    </div>
  )
}
