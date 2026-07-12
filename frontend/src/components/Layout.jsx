import { AnimatePresence, motion } from 'framer-motion'
import { Activity, BrainCircuit, Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { endpoints } from '../api/client'
import { navItems } from '../data/navigation'
import { useApp } from '../context/AppContext'

export default function Layout() {
  const [open,setOpen]=useState(false); const [status,setStatus]=useState('checking'); const location=useLocation(); const {compact,reducedMotion}=useApp()
  useEffect(()=>{ endpoints.health().then(r=>setStatus(r.data.status)).catch(()=>setStatus('offline')) },[location.pathname])
  useEffect(()=>setOpen(false),[location.pathname])
  return <div className={`app-shell ${compact?'compact':''}`}>
    <div className="ambient ambient-one"/><div className="ambient ambient-two"/>
    <aside className={`sidebar ${open?'sidebar-open':''}`}>
      <div className="brand"><div className="brand-mark"><BrainCircuit size={23}/></div><div><strong>RouteForge</strong><span>AMD AI Control Center</span></div><button className="mobile-close" onClick={()=>setOpen(false)}><X/></button></div>
      <nav>{navItems.map(({to,label,icon:Icon})=><NavLink key={to} to={to} className={({isActive})=>`nav-link ${isActive?'active':''}`}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-foot"><div className={`status-light status-${status}`}/><div><strong>{status==='offline'?'Backend offline':status==='checking'?'Checking backend':`System ${status}`}</strong><span>FastAPI · ROCm ready</span></div></div>
    </aside>
    {open && <div className="sidebar-scrim" onClick={()=>setOpen(false)}/>} 
    <main className="main"><header className="topbar"><button className="menu-btn" onClick={()=>setOpen(true)}><Menu/></button><div className="crumb"><Activity size={15}/><span>SLM-Based Intelligent Multi-Model Router</span></div><div className={`connection connection-${status}`}><span/>{status}</div></header>
      <AnimatePresence mode="wait"><motion.div key={location.pathname} initial={reducedMotion?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={reducedMotion?{}:{opacity:0,y:-5}} transition={{duration:.24}}><Outlet/></motion.div></AnimatePresence>
    </main>
  </div>
}
