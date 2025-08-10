import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import Documents from './components/Documents';  // ← Nuovo import
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Header />
          <main className="main-content">
            <Routes>
              {/* Route pubbliche */}
              <Route path="/login" element={<LoginForm />} />
              <Route path="/register" element={<RegisterForm />} />
              
              {/* Route protette */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Documents />  {/* ← Ora la home è la gestione documenti */}
                </ProtectedRoute>
              } />
              
              <Route path="/documents" element={
                <ProtectedRoute>
                  <Documents />
                </ProtectedRoute>
              } />
              
              <Route path="/health" element={
                <ProtectedRoute>
                  <div style={{textAlign: 'center', padding: '50px'}}>
                    <h2>✅ Sistema Operativo</h2>
                    <p>Tutti i servizi funzionano correttamente.</p>
                  </div>
                </ProtectedRoute>
              } />
              
              {/* Redirect per route non trovate */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
