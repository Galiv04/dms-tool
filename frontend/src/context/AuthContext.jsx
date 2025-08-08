import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/auth'

const AuthContext = createContext(null)

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  // Carica utente se esiste token
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const userData = await authApi.getCurrentUser()
          setUser(userData)
        } catch (error) {
          console.error('Error loading user:', error)
          authApi.logout()
          setToken(null)
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [token])

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password)
      const { access_token, user: userData } = response
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setToken(access_token)
      setUser(userData)
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }

  const register = async (userData) => {
    try {
      const user = await authApi.register(userData)
      return { success: true, user }
    } catch (error) {
      console.error('Registration error:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      }
    }
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
    setToken(null)
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
