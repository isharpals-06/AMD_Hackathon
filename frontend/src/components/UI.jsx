import { motion } from 'framer-motion'
import { AlertTriangle, ArrowUpRight, Check, Copy, LoaderCircle, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { useApp } from '../context/AppContext'

export function Page({ title, eyebrow, description, actions, children }) {
  const { reducedMotion } = useApp()
  return <motion.div initial={reducedMotion ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="page">
    <div className="page-head"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>
    {children}
  </motion.div>
}

export function Panel({ children, className = '', glow = false }) { return <section className={`panel ${glow ? 'panel-glow' : ''} ${className}`}>{children}</section> }
export function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{children}</span> }
export function Button({ children, icon: Icon, variant = 'primary', className = '', ...props }) { return <button className={`btn btn-${variant} ${className}`} {...props}>{Icon && <Icon size={16} />}{children}</button> }
export function Metric({ label, value, meta, icon: Icon, tone='blue' }) { return <Panel className="metric-card"><div className={`metric-icon tone-${tone}`}>{Icon && <Icon size={20}/>}</div><div><span>{label}</span><strong>{value}</strong>{meta && <small>{meta}</small>}</div></Panel> }
export function Skeleton({ className='' }) { return <div className={`skeleton ${className}`} /> }
export function Empty({ title, text }) { return <Panel className="empty"><div className="empty-orb"/><h3>{title}</h3><p>{text}</p></Panel> }
export function ErrorState({ error, onRetry }) { return <Panel className="error-box"><AlertTriangle/><div><h3>{error?.title || 'Something went wrong'}</h3><p>{error?.detail}</p></div>{onRetry && <Button variant="ghost" icon={RefreshCw} onClick={onRetry}>Retry</Button>}</Panel> }
export function CopyButton({ text }) { const [done,setDone]=useState(false); const copy=async()=>{await navigator.clipboard.writeText(text||'');setDone(true);setTimeout(()=>setDone(false),1400)}; return <button className="icon-btn" onClick={copy} aria-label="Copy response">{done?<Check size={16}/>:<Copy size={16}/>}</button> }
export function LoadingLabel({ text='Working' }) { return <span className="loading-label"><LoaderCircle size={15} className="spin"/>{text}</span> }
export function LinkButton({ children }) { return <span className="link-button">{children}<ArrowUpRight size={14}/></span> }
