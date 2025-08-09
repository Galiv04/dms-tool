import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Non mostrare header nelle pagine di login/register
  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-brand">
          <Link to="/" className="brand-link">
            📋 DMS Tool
          </Link>
        </div>

        {user && (
          <>
            <nav className="header-nav">
              <Link 
                to="/documents" 
                className={`nav-link ${location.pathname === '/documents' || location.pathname === '/' ? 'active' : ''}`}
              >
                📄 Documenti
              </Link>
              <Link 
                to="/health" 
                className={`nav-link ${location.pathname === '/health' ? 'active' : ''}`}
              >
                🏥 Stato Sistema
              </Link>
            </nav>

            <div className="header-user">
              <div className="user-info">
                <span className="user-name">
                  👤 {user.display_name || user.email}
                </span>
                <span className="user-role">
                  {user.role === 'ADMIN' ? '🔧 Admin' : '👤 Utente'}
                </span>
              </div>
              <button 
                onClick={handleLogout} 
                className="logout-btn"
                title="Logout"
              >
                🚪 Esci
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
};

export default Header;
