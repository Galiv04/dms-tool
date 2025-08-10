"""
Router per gestione documenti
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.schemas import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.deps import get_current_user
from app.db.models import User
from app.services.documents import document_service
import os
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload di un nuovo documento"""
    try:
        document = document_service.create_document(db, file, current_user)
        
        return DocumentUploadResponse(
            document=DocumentResponse.model_validate(document),
            message=f"Documento '{file.filename}' caricato con successo"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'upload: {str(e)}"
        )

@router.get("/", response_model=List[DocumentListResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista documenti dell'utente corrente"""
    documents = document_service.get_user_documents(db, current_user)
    return [DocumentListResponse.model_validate(doc) for doc in documents]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni dettagli di un documento specifico"""
    document = document_service.get_document(db, document_id, current_user)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    return DocumentResponse.model_validate(document)

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download di un documento"""
    document = document_service.get_document(db, document_id, current_user)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    file_path = document_service.get_file_path(document)
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File fisico non trovato"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type=document.content_type
    )

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview inline di un documento (se supportato)"""
    document = document_service.get_document(db, document_id, current_user)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    if not document_service.is_preview_supported(document):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preview non supportata per questo tipo di file"
        )
    
    file_path = document_service.get_file_path(document)
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File fisico non trovato"
        )
    
    # Per preview inline, non forziamo il download
    return FileResponse(
        path=str(file_path),
        media_type=document.content_type,
        headers={"Content-Disposition": "inline"}
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un documento"""
    success = document_service.delete_document(db, document_id, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    return {"message": "Documento eliminato con successo"}
