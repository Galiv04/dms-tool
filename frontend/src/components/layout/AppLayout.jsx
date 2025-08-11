// src/components/layout/AppLayout.jsx
import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopNavbar from './TopNavbar'
import { cn } from '../../lib/utils'

const AppLayout = ({ children }) => {
  const { isAuthenticated } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Non mostrare layout per pagine di auth
  const isAuthPage = ['/login', '/register'].includes(location.pathname)

  if (!isAuthenticated || isAuthPage) {
    return <div className="min-h-screen bg-background">{children}</div>
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onOpenChange={setSidebarOpen} />
      
      {/* Main Content */}
      <div className={cn(
        "transition-all duration-300 ease-in-out",
        "lg:ml-64", // Sidebar width on desktop
        sidebarOpen ? "ml-64" : "ml-0" // Mobile behavior
      )}>
        {/* Top Navbar */}
        <TopNavbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        {/* Page Content */}
        <main className="p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
      
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default AppLayout
