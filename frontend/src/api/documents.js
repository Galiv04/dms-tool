import apiClient from './client';

// Upload documento
export const uploadDocument = async (file, onUploadProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);

  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  };

  if (onUploadProgress) {
    config.onUploadProgress = (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onUploadProgress(percentCompleted);
    };
  }

  const response = await apiClient.post('/documents/upload', formData, config);
  return response.data;
};

// Lista documenti utente
export const getDocuments = async () => {
  const response = await apiClient.get('/documents/');
  return response.data;
};

// Dettagli documento
export const getDocument = async (documentId) => {
  const response = await apiClient.get(`/documents/${documentId}`);
  return response.data;
};

// Download documento
export const downloadDocument = async (documentId, filename) => {
  const response = await apiClient.get(`/documents/${documentId}/download`, {
    responseType: 'blob',
  });
  
  // Crea link per download
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

// Preview documento
export const previewDocument = async (documentId) => {
  const response = await apiClient.get(`/documents/${documentId}/preview`, {
    responseType: 'blob',
  });
  
  // Crea URL per preview inline
  const url = window.URL.createObjectURL(new Blob([response.data]));
  return url;
};

// Elimina documento
export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/documents/${documentId}`);
  return response.data;
};

// Utility per validazione file client-side
export const validateFile = (file) => {
  const maxSize = 50 * 1024 * 1024; // 50MB
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ];

  if (file.size > maxSize) {
    return { valid: false, error: 'File troppo grande. Massimo 50MB.' };
  }

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: `Tipo file ${file.type} non consentito.` };
  }

  return { valid: true };
};

// Utility per formattazione dimensione file
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Utility per icone tipo file
export const getFileIcon = (contentType) => {
  if (contentType.startsWith('image/')) return '🖼️';
  if (contentType === 'application/pdf') return '📄';
  if (contentType.includes('word')) return '📝';
  if (contentType.includes('excel') || contentType.includes('spreadsheet')) return '📊';
  if (contentType.includes('powerpoint') || contentType.includes('presentation')) return '📈';
  if (contentType === 'text/plain') return '📃';
  return '📄';
};
