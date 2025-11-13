import React, { useState } from 'react'

const AGENT_API = import.meta.env.VITE_AGENT_API || 'http://localhost:8000'

export default function App() {
  const [nl, setNl] = useState('')
  const [testIR, setTestIR] = useState<any>(null)
  const [log, setLog] = useState<string>('')
  const [showReport, setShowReport] = useState(false)
  const [report, setReport] = useState<any>(null)

  async function generate() {
    setLog('Generating...')
    const res = await fetch(`${AGENT_API}/generate_scenario`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ nl, target_url: '' })
    })
    const data = await res.json()
    setTestIR(data)
    setLog('Generated TestIR')
  }

  async function run() {
    setLog('Running...')
    const payload = { run_id: `run_${Math.random().toString(16).slice(2,10)}`, test_ir: testIR }
    const res = await fetch(`${AGENT_API}/run`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    })
    const data = await res.json()
    setLog(JSON.stringify(data, null, 2))
  }

  async function fetchReport(){
    setLog('Fetching report...')
    try{
      const res = await fetch(`${AGENT_API}/report`)
      const data = await res.json()
      setReport(data)
      setLog('Report loaded')
    }catch(err){
      setLog('Report fetch error: ' + err)
    }
  }

  return (
    <div style={{maxWidth:1000, margin:'40px auto', fontFamily:'Arial, sans-serif'}}>
      <h1>AI Test Platform — Frontend</h1>
      <div style={{display:'flex', gap:10, marginBottom:12}}>
        <button onClick={()=>setShowReport(false)}>Generator</button>
        <button onClick={()=>{setShowReport(true); fetchReport();}}>Reports</button>
      </div>

      {!showReport && (
        <div>
          <p>Enter natural language test description, generate TestIR, and run it.</p>

          <textarea value={nl} onChange={e=>setNl(e.target.value)} rows={4} style={{width:'100%'}} placeholder="e.g. Verify login flow for demo user" />
          <div style={{marginTop:8}}>
            <button onClick={generate} style={{marginRight:8}}>Generate Scenario</button>
            <button onClick={run} disabled={!testIR}>Run Test</button>
          </div>

          <h3>Test IR</h3>
          <pre style={{background:'#f6f6f6', padding:12}}>{testIR ? JSON.stringify(testIR, null, 2) : 'No Test IR yet'}</pre>

          <h3>Logs / Result</h3>
          <pre style={{background:'#000', color:'#0f0', padding:12, minHeight:120}}>{log}</pre>
        </div>
      )}

      {showReport && (
        <div>
          <h2>Reports</h2>
          {!report && <div>No report yet. Click Refresh.</div>}
          {report && (
            <div>
              <h3>Summary</h3>
              <p>{report.summary}</p>
              <h3>Metrics</h3>
              <pre style={{background:'#f6f6f6', padding:12}}>{JSON.stringify(report.metrics, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
