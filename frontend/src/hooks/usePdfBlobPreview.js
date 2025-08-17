import { useState, useEffect } from 'react'
import apiClient from '@/api/client' // Importa il tuo client che già gestisce il token

export const usePdfBlobPreview = (documentId, enabled = true) => {
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!documentId || !enabled) return

    let revoke = null
    setLoading(true)
    setError(null)
    setPreviewUrl(null)

    apiClient.get(`/documents/${documentId}/preview`, { responseType: 'blob' })
      .then(res => {
        const url = URL.createObjectURL(res.data)
        setPreviewUrl(url)
        revoke = url
      })
      .catch(() => {
        setError("Errore preview PDF o permessi insufficienti")
        setPreviewUrl(null)
      })
      .finally(() => setLoading(false))

    return () => {
      revoke && URL.revokeObjectURL(revoke)
    }
  }, [documentId, enabled])

  return { previewUrl, loading, error }
}
