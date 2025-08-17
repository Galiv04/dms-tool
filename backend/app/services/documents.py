"""
Service per gestione documenti
"""
from typing import List, Optional, BinaryIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.db.models import Document, User
from app.db.schemas import DocumentResponse, DocumentListResponse
from app.services.storage import storage_service


class DocumentService:
    """Servizio per gestione documenti"""

    def __init__(self):
        self.storage = storage_service

    def create_document(
        self,
        db: Session,
        file: UploadFile,
        owner: User
    ) -> Document:
        """
        Crea un nuovo documento con upload file
        """
        # Validazione file
        file_size = 0
        file.file.seek(0, 2)  # Vai alla fine del file
        file_size = file.file.tell()  # Ottieni la posizione (= dimensione)
        file.file.seek(0)  # Torna all'inizio

        is_valid, error_msg = self.storage.validate_file(
            file.filename,
            file.content_type or "application/octet-stream",
            file_size
        )

        if not is_valid:
            raise ValueError(f"File non valido: {error_msg}")

        # Salva file nel storage
        document_id, storage_path, actual_size, file_hash = self.storage.save_file(
            file.file,
            file.filename,
            file.content_type or "application/octet-stream"
        )

        # Crea record nel database
        db_document = Document(
            id=document_id,
            owner_id=owner.id,
            filename=file.filename,
            original_filename=file.filename,
            storage_path=storage_path,
            content_type=file.content_type or "application/octet-stream",
            size=actual_size,
            file_hash=file_hash
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return db_document

    def get_document(self, db: Session, document_id: str, user: User) -> Optional[Document]:
        """
        Recupera documento se l'utente ha i permessi
        """
        document = db.query(Document).filter(
            Document.id == document_id).first()
        if not document:
            return None

        # Controllo permessi: proprietario può sempre accedere
        if document.owner_id == user.id:
            return document

        # 🆕 NUOVO: Recipients delle approvazioni possono accedere
        from app.db.models import ApprovalRequest, ApprovalRecipient, ApprovalStatus

        # Verifica se l'utente è un recipient di una richiesta di approvazione attiva
        recipient_access = db.query(ApprovalRecipient).join(
            ApprovalRequest, ApprovalRecipient.approval_request_id == ApprovalRequest.id
        ).filter(
            ApprovalRequest.document_id == document_id,
            ApprovalRecipient.recipient_email == user.email,
            ApprovalRequest.status == ApprovalStatus.PENDING  # Solo se ancora attiva
        ).first()

        if recipient_access:
            return document

        # Nessun permesso
        return None

    def get_user_documents(self, db: Session, user: User) -> List[Document]:
        """
        Recupera tutti i documenti dell'utente
        """
        return db.query(Document).filter(Document.owner_id == user.id).order_by(Document.created_at.desc()).all()

    def delete_document(self, db: Session, document_id: str, user: User) -> bool:
        """
        Elimina documento se l'utente ha i permessi e non ci sono approvazioni attive
        """
        document = self.get_document(db, document_id, user)
        if not document:
            return False

        from app.db.models import ApprovalRequest, ApprovalStatus

        # Controlla se ci sono richieste di approvazione attive
        active_approval = db.query(ApprovalRequest).filter(
            ApprovalRequest.document_id == document_id,
            ApprovalRequest.status.in_([
                ApprovalStatus.PENDING,
                ApprovalStatus.APPROVED  # Anche approved per mantenere tracciabilità
            ])
        ).first()

        # Se c'è una approvazione attiva, solleva eccezione
        if active_approval:
            from app.utils.exceptions import ValidationError  # ← Import tuo esistente
            raise ValidationError(
                f"Impossibile eliminare il documento. "
                f"Esiste una richiesta di approvazione in stato '{active_approval.status.value}'. "
                f"Elimina prima la richiesta di approvazione."
            )

        # Elimina file fisico
        file_deleted = self.storage.delete_file(document_id)

        # Elimina record dal database
        db.delete(document)
        db.commit()

        return file_deleted

    def get_file_path(self, document: Document):
        """
        Ottieni il path fisico del file
        """
        return self.storage.get_file_path(document.id, document.filename)

    def is_preview_supported(self, document: Document) -> bool:
        """
        Verifica se il documento supporta preview
        """
        return self.storage.is_preview_supported(document.content_type)


# Istanza globale del service
document_service = DocumentService()
