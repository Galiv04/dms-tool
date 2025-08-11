// src/components/layout/TopNavbar.jsx
import React from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useLocation } from 'react-router-dom'
import { useApprovalStats } from '../../hooks/useApprovals' // ✅ Aggiungi questo import
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { 
  Menu, 
  Bell, 
  Search, 
  Plus,
  RefreshCw
} from 'lucide-react'

const TopNavbar = ({ onMenuClick }) => {
  const { user } = useAuth()
  const location = useLocation()
  
  // ✅ Usa dati reali per notifiche
  const { data: stats } = useApprovalStats()
  const notificationCount = stats?.my_pending_approvals || 0

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard'
      case '/documents': return 'Documenti'
      case '/approvals': return 'Approvazioni'
      case '/admin': return 'Amministrazione'
      case '/stats': return 'Statistiche'
      default: return 'DMS Tool'
    }
  }

  const getPageActions = () => {
    switch (location.pathname) {
      case '/documents':
        return (
          <Button size="sm" className="gap-2">
            <Plus className="h-4 w-4" />
            Carica Documento
          </Button>
        )
      case '/approvals':
        return (
          <Button size="sm" className="gap-2">
            <Plus className="h-4 w-4" />
            Nuova Approvazione
          </Button>
        )
      default:
        return null
    }
  }

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      {/* Left Side */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        <div>
          <h1 className="text-lg font-semibold">{getPageTitle()}</h1>
          <p className="text-sm text-muted-foreground hidden sm:block">
            Benvenuto, {user?.display_name || user?.email}
          </p>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" className="gap-2 hidden md:flex">
          <Search className="h-4 w-4" />
          Cerca...
        </Button>

        {/* ✅ Notifiche dinamiche */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-4 w-4" />
          {notificationCount > 0 && (
            <Badge 
              className="absolute -top-1 -right-1 h-5 w-5 p-0 text-xs"
              variant="destructive"
            >
              {notificationCount > 99 ? '99+' : notificationCount}
            </Badge>
          )}
        </Button>

        {getPageActions()}

        <Button variant="ghost" size="sm">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}

export default TopNavbar
