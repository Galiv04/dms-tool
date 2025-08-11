// src/hooks/useAuth.js - VERSIONE CORRETTA
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../api/auth' // ✅ Questo import è corretto

// Hook per user corrente
export const useCurrentUser = (token) => {
  return useQuery({
    queryKey: ['auth', 'currentUser'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: !!token,
    retry: false, // Non riprovare su 401
    staleTime: 5 * 60 * 1000, // 5 minuti
  })
}

// Hook per login
export const useLogin = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ email, password }) => authApi.login(email, password),
    onSuccess: (data) => {
      // Salva token
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      // Aggiorna cache user
      queryClient.setQueryData(['auth', 'currentUser'], data.user)
    },
    onError: (error) => {
      console.error('Login failed:', error)
    }
  })
}

// Hook per register
export const useRegister = () => {
  return useMutation({
    mutationFn: (userData) => authApi.register(userData),
    onError: (error) => {
      console.error('Registration failed:', error)
    }
  })
}

// Hook per logout
export const useLogout = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => {
      // authApi.logout() è sincrona, quindi wrappala
      authApi.logout()
      return Promise.resolve()
    },
    onSuccess: () => {
      // Pulisci tutta la cache
      queryClient.clear()
    }
  })
}
