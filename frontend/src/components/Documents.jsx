// src/components/Documents.jsx
import React, { useState } from 'react'
import DocumentUpload from './DocumentUpload'
import DocumentList from './DocumentList'
import { useAuth } from '../contexts/AuthContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CheckCircle, XCircle, Upload, Filter, X } from 'lucide-react'

const Documents = () => {
  const { user } = useAuth()
  const [uploadKey, setUploadKey] = useState(0)
  const [filters, setFilters] = useState({})
  const [notification, setNotification] = useState(null)

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const handleUploadSuccess = (document) => {
    showNotification(`${document.filename} caricato con successo!`, 'success')
    setUploadKey(prev => prev + 1)
  }

  const handleUploadError = (error) => {
    showNotification(`Errore upload: ${error}`, 'error')
  }

  const handleFilterChange = (value) => {
    // ✅ Fix: Gestisci correttamente il valore "all"
    if (value === 'all' || !value) {
      setFilters({})
    } else {
      setFilters({ type: value })
    }
  }

  const clearNotification = () => {
    setNotification(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestione Documenti</h1>
          <p className="text-muted-foreground">
            Benvenuto, {user?.display_name || user?.email}
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          {Object.keys(filters).length > 0 ? 'Filtri attivi' : 'Tutti i documenti'}
        </Badge>
      </div>

      {/* Notification */}
      {notification && (
        <Alert 
          variant={notification.type === 'error' ? 'destructive' : 'default'}
          className={`border-l-4 ${
            notification.type === 'success' 
              ? 'border-l-green-500 bg-green-50 text-green-800' 
              : notification.type === 'error'
              ? 'border-l-red-500 bg-red-50 text-red-800'
              : 'border-l-blue-500 bg-blue-50 text-blue-800'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {notification.type === 'success' && <CheckCircle className="h-4 w-4" />}
              {notification.type === 'error' && <XCircle className="h-4 w-4" />}
              <AlertDescription>
                {notification.message}
              </AlertDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearNotification}
              className="h-auto p-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Alert>
      )}

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Carica Nuovo Documento
          </CardTitle>
          <CardDescription>
            Trascina i file o clicca per selezionare. Formati supportati: PDF, DOC, TXT, Immagini
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentUpload
            key={uploadKey}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </CardContent>
      </Card>

      {/* Documents Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                I Tuoi Documenti
              </CardTitle>
              <CardDescription>
                Gestisci e visualizza tutti i tuoi documenti
              </CardDescription>
            </div>
            
            {/* ✅ Fix: Filters corretti */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select onValueChange={handleFilterChange} defaultValue="all">
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Filtra per tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i tipi</SelectItem>
                  <SelectItem value="application/pdf">PDF</SelectItem>
                  <SelectItem value="image/*">Immagini</SelectItem>
                  <SelectItem value="application/msword">Word</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <DocumentList filters={filters} />
        </CardContent>
      </Card>
    </div>
  )
}

export default Documents
