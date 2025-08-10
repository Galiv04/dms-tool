import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import './Documents.css';

const Documents = () => {
  const { user } = useAuth();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [notification, setNotification] = useState(null);

  const handleUploadSuccess = (result) => {
    console.log('Upload completato:', result);
    
    // Mostra notifica successo
    setNotification({
      type: 'success',
      message: result.message || 'Documento caricato con successo!'
    });

    // Refresh della lista documenti
    setRefreshTrigger(prev => prev + 1);

    // Nascondi notifica dopo 5 secondi
    setTimeout(() => {
      setNotification(null);
    }, 5000);
  };

  const handleUploadError = (error) => {
    console.error('Errore upload:', error);
    
    setNotification({
      type: 'error',
      message: error || 'Errore durante il caricamento del documento'
    });

    // Nascondi notifica dopo 5 secondi
    setTimeout(() => {
      setNotification(null);
    }, 5000);
  };

  const handleListError = (error) => {
    console.error('Errore lista:', error);
    
    setNotification({
      type: 'error',
      message: error
    });

    setTimeout(() => {
      setNotification(null);
    }, 5000);
  };

  const closeNotification = () => {
    setNotification(null);
  };

  return (
    <div className="documents-page">
      {/* Header della pagina */}
      <div className="documents-header">
        <h1>📄 Gestione Documenti</h1>
        <p>Benvenuto, <strong>{user?.display_name || user?.email}</strong>! Carica e gestisci i tuoi documenti.</p>
      </div>

      {/* Notifiche */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          <span className="notification-message">{notification.message}</span>
          <button 
            className="notification-close"
            onClick={closeNotification}
            aria-label="Chiudi notifica"
          >
            ×
          </button>
        </div>
      )}

      {/* Sezione Upload */}
      <section className="upload-section">
        <DocumentUpload
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      </section>

      {/* Sezione Lista Documenti */}
      <section className="documents-section">
        <DocumentList
          refreshTrigger={refreshTrigger}
          onError={handleListError}
        />
      </section>
    </div>
  );
};

export default Documents;
