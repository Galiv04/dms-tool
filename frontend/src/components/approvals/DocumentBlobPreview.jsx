import React from 'react'
import { usePdfBlobPreview } from '@/hooks/usePdfBlobPreview'

const DocumentBlobPreview = ({ document, showPreview }) => {
  const { previewUrl, loading, error } = usePdfBlobPreview(document.id, showPreview)

  // Mostra loading/error/iframe
  if (!showPreview) return null

  return (
    <div className="mt-3">
      {loading && (
        <div className="h-80 flex items-center justify-center">Caricamento preview...</div>
      )}

      {error && (
        <div className="h-80 flex items-center justify-center text-red-600">{error}</div>
      )}

      {!loading && !error && previewUrl && (
        <div className="h-80 border border-gray-200 rounded-md overflow-hidden">
          <iframe
            src={previewUrl + "#toolbar=0"}
            title="Anteprima documento"
            width="100%"
            height="100%"
            className="border-0"
          />
        </div>
      )}
    </div>
  )
}

export default DocumentBlobPreview
