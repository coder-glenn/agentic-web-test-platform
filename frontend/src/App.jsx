
import React, {useState, useEffect, useRef} from 'react'

export default function App(){
  const [nl, setNl] = useState('验证能在 playwright 官网导航到 Docs 并截图')
  const [runId, setRunId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [artifacts, setArtifacts] = useState([])
  const wsRef = useRef(null)

  async function submit(){
    setLoading(true)
    setLogs([])
    setArtifacts([])
    const res = await fetch('/api/submit', {method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({nl})})
    const j = await res.json()
    setRunId(j.run_id)
    setStatus('running')
    setLoading(false)
    // open websocket
    openWs(j.run_id)
  }

  function openWs(rid){
    if(wsRef.current){
      try{ wsRef.current.close() }catch(e){}
      wsRef.current = null
    }
    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.hostname
    const port = 8000 // backend port
    const url = `${scheme}://${host}:${port}/ws/${rid}`
    const ws = new WebSocket(url)
    ws.onopen = ()=>{
      appendLog({type:'info', message:'ws connected'})
    }
    ws.onmessage = (ev)=>{
      try{
        const data = JSON.parse(ev.data)
        handleWsMessage(data)
      }catch(e){ console.error('ws parse', e) }
    }
    ws.onclose = ()=>{ appendLog({type:'info', message:'ws closed'}) }
    ws.onerror = (e)=>{ appendLog({type:'error', message:'ws error'}) }
    wsRef.current = ws
  }

  function appendLog(item){
    setLogs(prev=>[...prev, item])
  }

  function handleWsMessage(msg){
    appendLog(msg)
    if(msg.type === 'artifact' && msg.url){
      // build absolute url based on backend host
      const host = window.location.hostname
      const port = 8000
      const scheme = window.location.protocol === 'https:' ? 'https' : 'http'
      const url = `${scheme}://${host}:${port}${msg.url}`
      setArtifacts(prev => [...prev, {step: msg.step, url}])
    }
    if(msg.type === 'run_end'){
      setStatus(msg.ok ? 'done' : 'failed')
      // fetch final result
      if(runId){
        fetch(`/api/result/${runId}`).then(r=>r.json()).then(j=>setResult(j))
      }
    }
  }

  useEffect(()=>{
    // cleanup websocket on unmount
    return ()=>{ if(wsRef.current) wsRef.current.close() }
  }, [])

  return (
    <div className="container">
      <header className="header">
        <h1>AI 驱动的 Web 自动化测试平台</h1>
        <p className="sub">输入自然语言，AI 自动生成并执行测试流程</p>
      </header>
      <main>
        <section className="card">
          <h2>提交测试需求</h2>
          <textarea value={nl} onChange={e=>setNl(e.target.value)} />
          <div style={{marginTop:10}}>
            <button className="btn" onClick={submit} disabled={loading}>提交测试</button>
            <button className="btn ghost" onClick={()=>{ setNl('验证能在 playwright 官网导航到 Docs 并截图') }}>恢复示例</button>
          </div>
        </section>
        <section className="card">
          <h2>运行信息</h2>
          <div style={{display:'flex',gap:12}}>
            <div>RunId: <strong>{runId||'-'}</strong></div>
            <div>Status: <strong>{status||'-'}</strong></div>
          </div>
          <div style={{display:'flex',gap:12,marginTop:12}}>
            <div style={{flex:1}}>
              <h3>实时日志</h3>
              <div className="logbox">
                {logs.length===0 ? <div className="muted">暂无日志</div> : logs.map((l,i)=>(
                  <div key={i} className="logline"><b>{l.type}</b> {l.message || l.step || JSON.stringify(l)}</div>
                ))}
              </div>
            </div>
            <div style={{width:260}}>
              <h3>截图预览</h3>
              <div className="thumbs">
                {artifacts.length===0 ? <div className="muted">暂无截图</div> : artifacts.map((a,i)=>(
                  <div key={i} className="thumb">
                    <div className="thumb-label">{a.step}</div>
                    <img src={a.url} alt={a.step} onError={(e)=>{ e.target.src=''; e.target.alt='failed' }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
          <pre style={{whiteSpace:'pre-wrap',marginTop:10}}>{result ? JSON.stringify(result, null, 2): '无结果'}</pre>
        </section>
      </main>
      <footer>Prototype • 小而美的界面 • 适合演示与扩展</footer>
    </div>
  )
}
