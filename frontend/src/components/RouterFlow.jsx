import { motion } from 'framer-motion'
import { Bot, Braces, CheckCircle2, Cloud, Database, GitBranch, MessageSquareText, Search } from 'lucide-react'
import { useApp } from '../context/AppContext'

const nodes = [
  { id:'prompt', label:'Incoming prompt', sub:'Request accepted', icon:MessageSquareText },
  { id:'slm', label:'Router SLM', sub:'Tier 1 classifier', icon:Bot },
  { id:'vector', label:'Vector search', sub:'Tier 2 semantic match', icon:Search },
  { id:'regex', label:'Regex fallback', sub:'Tier 3 safety net', icon:Braces },
  { id:'policy', label:'Routing policy', sub:'Task → model mapping', icon:GitBranch },
  { id:'execute', label:'Model execution', sub:'Local or cloud', icon:Cloud },
  { id:'persist', label:'Metrics log', sub:'SQLite WAL', icon:Database },
  { id:'done', label:'Final response', sub:'Tokens, cost, latency', icon:CheckCircle2 },
]

export default function RouterFlow({ active='idle', response }) {
  const { reducedMotion } = useApp()
  const routeTier = response?.classifierTier
  const isFallback = response?.metadata?.fallback_model_used
  const activeIndex = active === 'idle' ? -1 : active === 'classifying' ? 1 : active === 'routing' ? 4 : active === 'executing' ? 5 : active === 'complete' ? 7 : 0
  return <div className="router-flow">
    {nodes.map((node,index)=>{
      const Icon=node.icon
      const skipped = routeTier && ((node.id==='vector' && routeTier==='tier1') || (node.id==='regex' && routeTier!=='tier3'))
      const state = skipped ? 'skipped' : index < activeIndex ? 'complete' : index===activeIndex ? 'active' : 'idle'
      return <div className="flow-item" key={node.id}>
        <motion.div className={`flow-node flow-${state}`} animate={!reducedMotion && state==='active' ? { boxShadow:['0 0 0 rgba(34,211,238,0)','0 0 32px rgba(34,211,238,.32)','0 0 0 rgba(34,211,238,0)'] } : {}} transition={{repeat:Infinity,duration:1.8}}>
          <div className="flow-icon"><Icon size={20}/></div><div><strong>{node.label}</strong><span>{node.sub}</span></div>
          {node.id==='execute' && isFallback && <span className="fallback-pill">fallback</span>}
        </motion.div>
        {index<nodes.length-1 && <div className={`flow-line ${index<activeIndex?'flow-line-active':''}`}><motion.span animate={!reducedMotion && index<activeIndex?{x:['-20%','120%']}:{}} transition={{repeat:Infinity,duration:1.8,ease:'linear'}}/></div>}
      </div>
    })}
  </div>
}
