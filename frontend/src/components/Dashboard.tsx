import React, { useEffect, useState } from 'react'
import agentApi from '../api/agentApi'
import TaskList from './TaskList'
import ReportViewer from './ReportViewer'
import MetricCard from './MetricCard'

export default function Dashboard(){
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  async function fetchReport(){
    setLoading(true)
    try{
      const res = await agentApi.get('/report')
      setMetrics(res.data.metrics)
    }catch(e){
      console.error(e)
    }finally{setLoading(false)}
  }

  useEffect(()=>{fetchReport()}, [])

  return (
    <div style={{maxWidth:1100}}>
      <h2>Dashboard</h2>
      <div style={{display:'flex', gap:16}}>
        <MetricCard title="Total Tasks" value={metrics?.total_tasks ?? '-'} />
        <MetricCard title="Completed" value={metrics?.completed ?? '-'} />
        <MetricCard title="Failed" value={metrics?.failed ?? '-'} />
        <MetricCard title="Avg Duration (s)" value={metrics?.avg_duration_seconds ? metrics.avg_duration_seconds.toFixed(1) : '-'} />
      </div>

      <div style={{display:'flex', gap:20, marginTop:20}}>
        <div style={{flex:1}}>
          <TaskList />
        </div>
        <div style={{flex:1}}>
          <ReportViewer metrics={metrics} onRefresh={fetchReport} loading={loading} />
        </div>
      </div>
    </div>
  )
}