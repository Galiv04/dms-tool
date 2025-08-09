import React, { useState, useEffect } from 'react';
import { 
  getDocuments, 
  downloadDocument, 
  deleteDocument, 
  formatFileSize, 
  getFileIcon 
} from '../api/documents';
import './DocumentList.css';

const DocumentList = ({ refreshTrigger, onError }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Errore caricamento documenti:', error);
      if (onError) {
        onError('Errore nel caricamento dei documenti');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [refreshTrigger]);

  const handleDownload = async (document) => {
    try {
      await downloadDocument(document.id, document.original_filename);
    } catch (error) {
      console.error('Errore download:', error);
      if (onError) {
        onError('Errore durante il download');
      }
    }
  };

  const handleDelete = async (document) => {
    if (!window.confirm(`Sei sicuro di voler eliminare "${document.filename}"?`)) {
      return;
    }

    try {
      setDeletingId(document.id);
      await deleteDocument(document.id);
      
      // Ricarica la lista
      await loadDocuments();
    } catch (error) {
      console.error('Errore eliminazione:', error);
      if (onError) {
        onError('Errore durante l\'eliminazione');
      }
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="document-list">
        <h3>I Tuoi Documenti</h3>
        <div className="loading-placeholder">
          <div className="loading-spinner">⏳</div>
          <p>Caricamento documenti...</p>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="document-list">
        <h3>I Tuoi Documenti</h3>
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <h4>Nessun documento caricato</h4>
          <p>Carica il tuo primo documento utilizzando l'area di upload sopra.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="document-list">
      <h3>I Tuoi Documenti ({documents.length})</h3>
      
      <div className="documents-grid">
        {documents.map((document) => (
          <div key={document.id} className="document-card">
            <div className="document-header">
              <div className="file-icon">
                {getFileIcon(document.content_type)}
              </div>
              <div className="document-info">
                <h4 className="document-title" title={document.original_filename}>
                  {document.filename}
                </h4>
                <div className="document-meta">
                  <span className="file-size">{formatFileSize(document.size)}</span>
                  <span className="file-date">{formatDate(document.created_at)}</span>
                </div>
              </div>
            </div>

            <div className="document-actions">
              <button
                className="action-btn download-btn"
                onClick={() => handleDownload(document)}
                title="Scarica documento"
              >
                📥 Download
              </button>
              
              <button
                className="action-btn delete-btn"
                onClick={() => handleDelete(document)}
                disabled={deletingId === document.id}
                title="Elimina documento"
              >
                {deletingId === document.id ? '⏳' : '🗑️'} Elimina
              </button>
            </div>

            <div className="document-type">
              {document.content_type.split('/')[1].toUpperCase()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentList;
