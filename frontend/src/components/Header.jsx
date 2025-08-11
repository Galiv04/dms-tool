// src/components/Header.jsx - SEMPLIFICATO (ora usiamo AppLayout)
import React from 'react'
import { useLocation } from 'react-router-dom'

const Header = () => {
  const location = useLocation()
  
  // Il nuovo layout gestisce tutto - questo componente non è più necessario
  // ma lo manteniamo per compatibilità
  
  // Non mostrare header nelle pagine di login/register e quando usiamo il nuovo layout
  if (
    location.pathname === '/login' || 
    location.pathname === '/register' ||
    location.pathname === '/' ||
    location.pathname === '/documents' ||
    location.pathname === '/approvals' ||
    location.pathname === '/admin'
  ) {
    return null
  }

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <span className="font-bold">DMS Tool</span>
        </div>
      </div>
    </header>
  )
}

export default Header
