import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const OverviewPage = lazy(() => import('./pages/OverviewPage'))
const PlaygroundPage = lazy(() => import('./pages/PlaygroundPage'))
const RouterPage = lazy(() => import('./pages/RouterPage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const ArchitecturePage = lazy(() => import('./pages/ArchitecturePage'))
const HealthPage = lazy(() => import('./pages/HealthPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function Loader(){return <div className="route-loader"><div className="brand-mark">AI</div><span>Loading control center…</span></div>}
export default function App(){return <Suspense fallback={<Loader/>}><Routes><Route path="/" element={<LandingPage/>}/><Route element={<Layout/>}><Route path="/overview" element={<OverviewPage/>}/><Route path="/playground" element={<PlaygroundPage/>}/><Route path="/router" element={<RouterPage/>}/><Route path="/analytics" element={<AnalyticsPage/>}/><Route path="/history" element={<HistoryPage/>}/><Route path="/architecture" element={<ArchitecturePage/>}/><Route path="/health" element={<HealthPage/>}/><Route path="/settings" element={<SettingsPage/>}/></Route><Route path="*" element={<NotFoundPage/>}/></Routes></Suspense>}
