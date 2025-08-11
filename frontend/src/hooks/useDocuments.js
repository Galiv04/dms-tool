// src/hooks/useDocuments.js - VERSIONE CORRETTA
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  uploadDocument, 
  getDocuments, 
  deleteDocument, 
  downloadDocument,
  previewDocument,
  getDocument 
} from '../api/documents'

// Hook per lista documenti
export const useDocuments = (filters = {}) => {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: () => getDocuments(), // La tua getDocuments non prende filtri
    staleTime: 2 * 60 * 1000, // 2 minuti
    retry: 3,
  })
}

// Hook per upload documento
export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ file, onProgress }) => uploadDocument(file, onProgress),
    onSuccess: () => {
      // Invalida cache documenti dopo upload
      queryClient.invalidateQueries(['documents'])
    },
    onError: (error) => {
      console.error('Upload failed:', error)
    }
  })
}

// Hook per eliminazione documento
export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (documentId) => deleteDocument(documentId),
    onSuccess: () => {
      // Invalida lista documenti dopo eliminazione
      queryClient.invalidateQueries(['documents'])
    },
    onError: (error) => {
      console.error('Delete failed:', error)
    }
  })
}

// Hook per download documento
export const useDownloadDocument = () => {
  return useMutation({
    mutationFn: ({ documentId, filename }) => downloadDocument(documentId, filename),
    onError: (error) => {
      console.error('Download failed:', error)
    }
  })
}

// Hook per preview documento
export const useDocumentPreview = (documentId) => {
  return useQuery({
    queryKey: ['documents', documentId, 'preview'],
    queryFn: () => previewDocument(documentId),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // 5 minuti cache per preview
  })
}

// Hook per singolo documento
export const useDocument = (documentId) => {
  return useQuery({
    queryKey: ['documents', documentId],
    queryFn: () => getDocument(documentId),
    enabled: !!documentId,
  })
}
