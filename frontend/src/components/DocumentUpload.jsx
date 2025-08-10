import React, { useState, useRef } from 'react';
import { uploadDocument, validateFile } from '../api/documents';
import './DocumentUpload.css';

const DocumentUpload = ({ onUploadSuccess, onUploadError }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
    // Reset input per permettere re-upload dello stesso file
    e.target.value = '';
  };

  const handleFileUpload = async (file) => {
    // Validazione client-side
    const validation = validateFile(file);
    if (!validation.valid) {
      setUploadStatus(`Errore: ${validation.error}`);
      if (onUploadError) {
        onUploadError(validation.error);
      }
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus(`Caricando ${file.name}...`);

    try {
      const result = await uploadDocument(file, (progress) => {
        setUploadProgress(progress);
        setUploadStatus(`Caricando ${file.name}... ${progress}%`);
      });

      setUploadStatus(`✅ ${file.name} caricato con successo!`);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

      // Reset dopo successo
      setTimeout(() => {
        setUploadStatus('');
        setUploadProgress(0);
      }, 3000);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Errore durante l\'upload';
      setUploadStatus(`❌ Errore: ${errorMessage}`);
      
      if (onUploadError) {
        onUploadError(errorMessage);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const openFileSelector = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="document-upload">
      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileSelector}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.xls,.xlsx,.ppt,.pptx"
          style={{ display: 'none' }}
        />

        {!isUploading ? (
          <>
            <div className="upload-icon">📤</div>
            <div className="upload-text">
              <h3>Carica Documento</h3>
              <p>Trascina i file qui o <span className="click-text">clicca per selezionare</span></p>
              <small>PDF, DOC, TXT, Immagini - Massimo 50MB</small>
            </div>
          </>
        ) : (
          <div className="upload-progress">
            <div className="progress-circle">
              <div className="progress-text">{uploadProgress}%</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {uploadStatus && (
        <div className={`upload-status ${uploadStatus.includes('❌') ? 'error' : uploadStatus.includes('✅') ? 'success' : 'info'}`}>
          {uploadStatus}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
