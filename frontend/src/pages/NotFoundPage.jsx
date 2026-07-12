import { ArrowLeft, BrainCircuit } from 'lucide-react'
import { Link } from 'react-router-dom'
export default function NotFoundPage(){return <div className="not-found"><div className="brand-mark"><BrainCircuit/></div><span>404 · ROUTE NOT FOUND</span><h1>This path wasn’t in the routing policy.</h1><p>Return to the control center and choose a valid destination.</p><Link className="btn btn-primary" to="/overview"><ArrowLeft/> Back to overview</Link></div>}
