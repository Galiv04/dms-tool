// src/components/DocumentList.jsx
import React, { useState } from 'react'
import { useDocuments, useDeleteDocument, useDownloadDocument } from '../hooks/useDocuments'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  FileText, 
  Download, 
  Trash2, 
  RefreshCw, 
  AlertCircle,
  File,
  Image,
  FileSpreadsheet,
  Loader2
} from 'lucide-react'

const DocumentList = ({ filters = {} }) => {
  const [selectedDocument, setSelectedDocument] = useState(null)
  
  // React Query hooks
  const { 
    data: documents, 
    isLoading, 
    error, 
    refetch,
    isFetching 
  } = useDocuments(filters)
  
  const deleteMutation = useDeleteDocument()
  const downloadMutation = useDownloadDocument()

  const handleDelete = async (document) => {
    if (window.confirm(`Sei sicuro di voler eliminare "${document.filename}"?`)) {
      try {
        await deleteMutation.mutateAsync(document.id)
      } catch (error) {
        alert(`Errore nell'eliminazione: ${error.message}`)
      }
    }
  }

  const handleDownload = async (document) => {
    try {
      await downloadMutation.mutateAsync({
        documentId: document.id,
        filename: document.filename
      })
    } catch (error) {
      alert(`Errore nel download: ${error.message}`)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFileIcon = (contentType) => {
    if (contentType?.includes('pdf')) return <FileText className="h-5 w-5 text-red-500" />
    if (contentType?.includes('image')) return <Image className="h-5 w-5 text-green-500" />
    if (contentType?.includes('spreadsheet') || contentType?.includes('excel')) return <FileSpreadsheet className="h-5 w-5 text-green-600" />
    return <File className="h-5 w-5 text-blue-500" />
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Caricamento documenti...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>Errore nel caricamento dei documenti: {error.message}</span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Riprova
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="rounded-full bg-muted/50 w-16 h-16 flex items-center justify-center mx-auto mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Nessun documento trovato</h3>
        <p className="text-muted-foreground mb-4">
          Carica il tuo primo documento per iniziare
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            Documenti ({documents.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            Gestisci i tuoi file caricati
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      {/* Documents Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc) => (
          <Card 
            key={doc.id} 
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedDocument?.id === doc.id ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => setSelectedDocument(doc)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {getFileIcon(doc.content_type)}
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-sm truncate" title={doc.filename}>
                      {doc.filename}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {doc.content_type}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className="space-y-3">
                {/* File Info */}
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{formatFileSize(doc.file_size)}</span>
                  <span>{formatDate(doc.created_at)}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDownload(doc)
                    }}
                    disabled={downloadMutation.isPending}
                    className="flex-1"
                  >
                    {downloadMutation.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Download className="h-3 w-3" />
                    )}
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(doc)
                    }}
                    disabled={deleteMutation.isPending}
                    className="flex-1 text-destructive hover:text-destructive"
                  >
                    {deleteMutation.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default DocumentList
