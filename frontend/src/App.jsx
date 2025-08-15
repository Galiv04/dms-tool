// src/App.jsx
import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import LoginForm from './components/LoginForm'
import RegisterForm from './components/RegisterForm'
import Documents from './components/Documents'
import ProtectedRoute from './components/ProtectedRoute'
import ApprovalDashboard from './pages/ApprovalDashboard'
import AppLayout from './components/layout/AppLayout'
import { Toaster } from "./components/ui/sonner"

function App() {
  const { isAuthenticated, loading } = useAuth()

  // Loading state mentre verifica autenticazione
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-sm text-muted-foreground">Caricamento applicazione...</p>
        </div>
      </div>
    )
  }

  return (
    <AppLayout>
      <Routes>
        {/* Route pubbliche */}
        <Route 
          path="/login" 
          element={
            !isAuthenticated ? (
              <LoginForm />
            ) : (
              <Navigate to="/" replace />
            )
          } 
        />
        
        <Route 
          path="/register" 
          element={
            !isAuthenticated ? (
              <RegisterForm />
            ) : (
              <Navigate to="/" replace />
            )
          } 
        />

        {/* Route protette */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <div className="space-y-6">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                  <p className="text-muted-foreground">
                    Panoramica del tuo Document Management System
                  </p>
                </div>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <svg className="h-4 w-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-2xl font-bold">24</p>
                        <p className="text-xs text-muted-foreground">Documenti</p>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="flex items-center space-x-2">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <svg className="h-4 w-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-2xl font-bold">7</p>
                        <p className="text-xs text-muted-foreground">In Attesa</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/documents" 
          element={
            <ProtectedRoute>
              <Documents />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/approvals" 
          element={
            <ProtectedRoute>
              <ApprovalDashboard />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/admin" 
          element={
            <ProtectedRoute>
              <div className="space-y-6">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">Amministrazione</h1>
                  <p className="text-muted-foreground">
                    Pannello di controllo sistema
                  </p>
                </div>
                <div className="rounded-lg border bg-card p-6">
                  <h2 className="text-xl font-semibold mb-2">⚙️ Admin Dashboard</h2>
                  <p className="text-muted-foreground">Pannello amministrazione in arrivo...</p>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/health" 
          element={
            <div className="rounded-lg border bg-card p-6">
              <h2 className="text-2xl font-bold text-green-600">✅ Sistema Operativo</h2>
              <p className="text-muted-foreground">
                Tutti i servizi funzionano correttamente.
              </p>
            </div>
          } 
        />

        <Route 
          path="*" 
          element={<Navigate to="/" replace />} 
        />
      </Routes>
      <Toaster 
        position="top-right"
        richColors 
        closeButton 
      />
    </AppLayout>
  )
}

export default App
