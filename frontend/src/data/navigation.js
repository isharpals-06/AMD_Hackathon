import { Activity, BarChart3, Bot, Boxes, Gauge, History, Network, Settings } from 'lucide-react'
export const navItems = [
  { to: '/overview', label: 'Overview', icon: Gauge },
  { to: '/playground', label: 'AI Playground', icon: Bot },
  { to: '/router', label: 'Live Router', icon: Network },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/history', label: 'Session History', icon: History },
  { to: '/architecture', label: 'Architecture', icon: Boxes },
  { to: '/health', label: 'System Health', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
]
