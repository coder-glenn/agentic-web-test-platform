import React, { useState } from 'react'
import agentApi from '../api/agentApi'

export default function Generator(){
  const [nl, setNl] = useState('')
  const [testIR, setTestIR] = useState<any>(null)
  const [log, setLog] = useState('')

  async function generate(){
    setLog('Generating...')
    try{
      const res = await agentApi.post('/generate_scenario', { nl, target_url: '' })
      setTestIR(res.data)
      setLog('Generated TestIR')
    }catch(e:any){
      setLog('Error: ' + (e?.message||e))
    }
  }

  async function run(){
    setLog('Running...')
    try{
      const payload = { run_id: `run_${Math.random().toString(16).slice(2,10)}`, test_ir: testIR }
      const res = await agentApi.post('/run', payload)
      setLog(JSON.stringify(res.data, null, 2))
    }catch(e:any){
      setLog('Run error: ' + (e?.response?.data || e?.message || e))
    }
  }

  return (
    <div style={{maxWidth:900}}>
      <h2>Scenario Generator</h2>
      <textarea value={nl} onChange={e=>setNl(e.target.value)} rows={4} style={{width:'100%'}} placeholder="e.g. Test checkout flow" />
      <div style={{marginTop:8}}>
        <button onClick={generate} style={{marginRight:8}}>Generate Scenario</button>
        <button onClick={run} disabled={!testIR}>Run Test</button>
      </div>

      <h3 style={{marginTop:16}}>Test IR</h3>
      <pre style={{background:'#f6f6f6', padding:12}}>{testIR ? JSON.stringify(testIR, null, 2) : 'No Test IR yet'}</pre>

      <h3>Logs</h3>
      <pre style={{background:'#000', color:'#0f0', padding:12, minHeight:120}}>{log}</pre>
    </div>
  )
}