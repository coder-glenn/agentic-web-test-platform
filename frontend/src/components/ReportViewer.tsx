import React from 'react'

export default function ReportViewer({metrics, onRefresh, loading}:{metrics:any, onRefresh:()=>void, loading:boolean}){
  return (
    <div style={{border:'1px solid #eee', padding:12}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h3>Report</h3>
        <button onClick={onRefresh}>Refresh</button>
      </div>
      {loading && <div>Loading...</div>}
      {!metrics && !loading && <div>No metrics yet.</div>}
      {metrics && (
        <div>
          <p><strong>Success Rate:</strong> {metrics.total_tasks ? ((metrics.completed/Math.max(1,metrics.total_tasks))*100).toFixed(1)+'%' : 'N/A'}</p>
          <h4>Failure Distribution</h4>
          <ul>
            {Object.entries(metrics.failure_distribution||{}).map(([k,v])=> <li key={k}>{k}: {v}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}