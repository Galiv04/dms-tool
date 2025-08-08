import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    display_name: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long')
      setLoading(false)
      return
    }

    const result = await register(formData)
    
    if (result.success) {
      alert('Registration successful! Please login.')
      navigate('/login')
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="auth-form">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label>Display Name:</label>
          <input
            type="text"
            name="display_name"
            value={formData.display_name}
            onChange={handleChange}
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            disabled={loading}
            minLength="6"
          />
        </div>

        {error && <div className="error-message">{error}</div>}
        
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      
      <p>
        Already have an account? <a href="/login">Login here</a>
      </p>
    </div>
  )
}

export default RegisterForm
