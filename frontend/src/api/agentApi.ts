import axios from 'axios'

const AGENT_API = import.meta.env.VITE_AGENT_API || 'http://localhost:8000'

const client = axios.create({ baseURL: AGENT_API, timeout: 30_000 })

export default client

// frontend/src/hooks/useAgentStatus.ts
import { useEffect, useState } from 'react'
import agentApi from '../api/agentApi'

export default function useAgentStatus(poll=5000){
  const [status, setStatus] = useState<any>(null)
  useEffect(()=>{
    let mounted=true
    async function load(){
      try{
        const res = await agentApi.get('/tasks')
        if(mounted) setStatus({tasks:res.data})
      }catch(e){ }
    }
    load(); const id=setInterval(load,poll)
    return ()=>{ mounted=false; clearInterval(id) }
  }, [poll])
  return status
}