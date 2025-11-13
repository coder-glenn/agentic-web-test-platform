import React, { useEffect, useState } from 'react'
import agentApi from '../api/agentApi'

export default function TaskList(){
  const [tasks, setTasks] = useState<any[]>([])

  async function load(){
    try{
      const res = await agentApi.get('/tasks')
      setTasks(res.data)
    }catch(e){console.error(e)}
  }

  useEffect(()=>{load(); const id=setInterval(load,5000); return ()=>clearInterval(id)}, [])

  return (
    <div style={{border:'1px solid #eee', padding:12}}>
      <h3>Recent Tasks</h3>
      <ul>
        {tasks.slice().reverse().map(t=> (
          <li key={t.id} style={{marginBottom:8}}>
            <strong>{t.id.slice(0,8)}</strong> — {t.status} — {t.description || '-'} <br/>
            <small>updated: {t.updated_at}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}