// src/components/layout/Sidebar.jsx - AGGIORNA QUESTA PARTE
import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useApprovalStats } from '../../hooks/useApprovals' // ✅ Aggiungi questo
import { useDocuments } from '../../hooks/useDocuments'     // ✅ Aggiungi questo
import { Button } from '../ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar'
import { Badge } from '../ui/badge'
import { Separator } from '../ui/separator'
import { 
  FileText, 
  CheckSquare, 
  Settings, 
  Home, 
  BarChart3,
  LogOut,
  User,
  Bell,
  Shield
} from 'lucide-react'
import { cn } from '../../lib/utils'

const Sidebar = ({ open, onOpenChange }) => {
  const { user, logout } = useAuth()
  const location = useLocation()
  
  // ✅ Usa dati reali per i badge
  const { data: stats } = useApprovalStats()
  const { data: documents } = useDocuments()
  
  const navigationItems = [
    {
      title: 'Dashboard',
      href: '/',
      icon: Home,
      badge: null
    },
    {
      title: 'Documenti',
      href: '/documents',
      icon: FileText,
      badge: documents?.length || null // ✅ Conta documenti reali
    },
    {
      title: 'Approvazioni',
      href: '/approvals',
      icon: CheckSquare,
      badge: stats?.my_pending_approvals || null // ✅ Approvazioni pendenti reali
    },
    {
      title: 'Statistiche',
      href: '/stats',
      icon: BarChart3,
      badge: null
    },
    {
      title: 'Amministrazione',
      href: '/admin',
      icon: Shield,
      badge: user?.is_admin ? 'Admin' : null // ✅ Badge solo se admin
    }
  ]

  const handleLogout = () => {
    logout()
    onOpenChange(false)
  }

  return (
    <div className={cn(
      "fixed left-0 top-0 z-30 h-full w-64 transform bg-card border-r transition-transform duration-300 ease-in-out lg:translate-x-0",
      open ? "translate-x-0" : "-translate-x-full"
    )}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-16 items-center gap-3 border-b px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h1 className="font-semibold text-sm">DMS Tool</h1>
            <p className="text-xs text-muted-foreground">Document Management</p>
          </div>
        </div>

        {/* User Info */}
        <div className="p-6 pb-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={user?.avatar} alt={user?.display_name} />
              <AvatarFallback className="bg-primary text-primary-foreground">
                {user?.display_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.display_name || 'Utente'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
          </div>
        </div>

        <Separator />

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-4">
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            
            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => onOpenChange(false)}
                className={cn(
                  "flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive 
                    ? "bg-primary text-primary-foreground" 
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </div>
                {/* ✅ Mostra badge solo se non null */}
                {item.badge && (
                  <Badge 
                    variant={isActive ? "secondary" : "outline"}
                    className="h-5 px-1.5 text-xs"
                  >
                    {item.badge}
                  </Badge>
                )}
              </Link>
            )
          })}
        </nav>

        <Separator />

        {/* Footer Actions */}
        <div className="p-4 space-y-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3 text-muted-foreground"
            asChild
          >
            <Link to="/profile">
              <User className="h-4 w-4" />
              Profilo
            </Link>
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3 text-muted-foreground"
          >
            <Bell className="h-4 w-4" />
            Notifiche
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3 text-muted-foreground"
            asChild
          >
            <Link to="/settings">
              <Settings className="h-4 w-4" />
              Impostazioni
            </Link>
          </Button>
          
          <Separator className="my-2" />
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start gap-3 text-destructive hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
