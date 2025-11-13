import React from 'react'

export default function MetricCard({title, value}:{title:string, value:any}){
  return (
    <div style={{flex:1, padding:12, border:'1px solid #ddd', borderRadius:6}}>
      <div style={{fontSize:12, color:'#666'}}>{title}</div>
      <div style={{fontSize:20, fontWeight:600}}>{value}</div>
    </div>
  )
}