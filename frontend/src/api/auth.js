import apiClient from './client'

export const authApi = {
  register: async (userData) => {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  },

  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
}
