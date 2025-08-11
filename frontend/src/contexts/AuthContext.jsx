// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useCurrentUser, useLogin, useRegister, useLogout } from '../hooks/useAuth'

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
  const [token, setToken] = useState(localStorage.getItem('token'))
  // eslint-disable-next-line no-unused-vars
  const queryClient = useQueryClient()
  
  // Query per user corrente
  const { 
    data: user, 
    isLoading: loading, 
    error,
    refetch: refetchUser 
  } = useCurrentUser(token)
  
  // Mutations
  const loginMutation = useLogin()
  const registerMutation = useRegister()
  const logoutMutation = useLogout()

  // Gestisci errori di autenticazione
  useEffect(() => {
    if (error?.status === 401 || error?.response?.status === 401) {
      // Token scaduto o invalido
      handleLogout()
    }
  }, [error])

  // Gestisci successo login
  useEffect(() => {
    if (loginMutation.isSuccess && loginMutation.data) {
      setToken(loginMutation.data.access_token)
    }
  }, [loginMutation.isSuccess, loginMutation.data])

  const login = async (email, password) => {
    try {
      const result = await loginMutation.mutateAsync({ email, password })
      return { success: true, user: result.user }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }

  const register = async (userData) => {
    try {
      const user = await registerMutation.mutateAsync(userData)
      return { success: true, user }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      }
    }
  }

  const handleLogout = () => {
    setToken(null)
    logoutMutation.mutate()
  }

  const value = {
    user,
    token,
    loading: loading || loginMutation.isPending || registerMutation.isPending,
    login,
    register,
    logout: handleLogout,
    isAuthenticated: !!user && !!token,
    
    // Stati mutations per UI feedback
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    
    // Utility functions
    refetchUser
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
