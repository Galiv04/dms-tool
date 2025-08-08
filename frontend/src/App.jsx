import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginForm from './components/LoginForm'
import RegisterForm from './components/RegisterForm'
import ProtectedRoute from './components/ProtectedRoute'
import axios from 'axios'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  )
}

function AppContent() {
  const { user, logout, loading } = useAuth()
  const [healthStatus, setHealthStatus] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get('http://localhost:8000/health')
        setHealthStatus(response.data)
      // eslint-disable-next-line no-unused-vars
      } catch (error) {
        setHealthStatus({ status: 'error', message: 'Backend not reachable' })
      }
    }
    checkHealth()
  }, [])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>DMS Tool</h1>
        <div className="health-status">
          Backend Status: {healthStatus ? 
            <span className={healthStatus.status === 'ok' ? 'status-ok' : 'status-error'}>
              {healthStatus.message}
            </span> 
            : 'Checking...'}
        </div>
        
        {user && (
          <div className="user-info">
            Welcome, {user.display_name || user.email}!
            <button onClick={logout} className="logout-btn">Logout</button>
          </div>
        )}
      </header>
      
      <main>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          } />
          <Route path="/health" element={
            <ProtectedRoute>
              <HealthPage healthStatus={healthStatus} />
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  )
}

function Home() {
  const { user } = useAuth()
  
  return (
    <div>
      <h2>Welcome to DMS Tool</h2>
      <p>Hello, {user.display_name || user.email}!</p>
      <p>Document Management System with approval workflow</p>
    </div>
  )
}

function HealthPage({ healthStatus }) {
  return (
    <div>
      <h2>System Health</h2>
      <pre>{JSON.stringify(healthStatus, null, 2)}</pre>
    </div>
  )
}

export default App
