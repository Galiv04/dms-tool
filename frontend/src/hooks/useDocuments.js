import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  uploadDocument, 
  getDocuments, 
  deleteDocument, 
  downloadDocument,
  previewDocument,
  getDocument 
} from '../api/documents'
import { toast } from 'sonner'


// Hook per lista documenti
export const useDocuments = (filters = {}) => {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: () => getDocuments(), // La tua getDocuments non prende filtri
    staleTime: 2 * 60 * 1000, // 2 minuti
    retry: 3,
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, onProgress }) => uploadDocument(file, onProgress),
    onSuccess: (data) => {
      queryClient.invalidateQueries(['documents'])
      // 🔧 Sonner toast success
      toast.success(`Documento "${data.document.original_filename}" caricato con successo`)
    },
    onError: (error) => {
      console.error('Upload failed:', error)
      const errorMessage = error.response?.data?.detail || 'Errore durante il caricamento'
      
      // 🔧 Sonner toast error
      toast.error(`Errore upload: ${errorMessage}`)
    }
  })
}

export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (documentId) => {
      // 🔍 AGGIUNGI debug
      console.log('🔍 useDeleteDocument mutationFn called with:', documentId);
      console.log('🔍 typeof documentId:', typeof documentId);
      
      if (!documentId || documentId === 'undefined') {
        throw new Error('Document ID is undefined or invalid');
      }
      
      return deleteDocument(documentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['documents'])
      toast.success("Documento eliminato con successo")
    },
    onError: (error) => {
      console.error('Delete failed:', error)
      
      let errorMessage = "Errore durante l'eliminazione del documento"
      
      if (error.message === 'Document ID is undefined or invalid') {
        errorMessage = "Errore: ID documento non valido";
      } else if (error.response?.status === 400 && error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      toast.error(errorMessage)
    }
  })
}

export const useDownloadDocument = () => {
  return useMutation({
    mutationFn: ({ documentId, filename }) => downloadDocument(documentId, filename),
    onSuccess: (_, { filename }) => {
      toast.success(`Download di "${filename}" completato`)
    },
    onError: (error) => {
      console.error('Download failed:', error)
      const errorMessage = error.response?.data?.detail || 'Errore durante il download'
      toast.error(errorMessage)
    }
  })
}


export const useDocumentPreview = (documentId) => {
  return useQuery({
    queryKey: ['documents', documentId, 'preview'],
    queryFn: () => previewDocument(documentId),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000,
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || 'Errore nel caricamento preview'
      
      toast({
        title: "Errore preview",
        description: errorMessage,
        variant: "destructive",
      })
    }
  })
}

export const useDocument = (documentId) => {
  return useQuery({
    queryKey: ['documents', documentId],
    queryFn: () => getDocument(documentId),
    enabled: !!documentId,
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || 'Errore nel caricamento documento'
      
      toast({
        title: "Errore documento",
        description: errorMessage,
        variant: "destructive",
      })
    }
  })
}