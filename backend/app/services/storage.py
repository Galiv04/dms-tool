"""
Service per gestione storage locale dei documenti
"""
import os
import uuid
import shutil
from typing import Tuple, Optional, BinaryIO
from pathlib import Path
import mimetypes
import hashlib

class StorageService:
    """Servizio per gestione storage locale dei documenti"""
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Configurazione validazione
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.xls', '.xlsx', '.ppt', '.pptx'
        }
        self.allowed_mime_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'application/rtf',
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
    
    def validate_file(self, filename: str, content_type: str, size: int) -> Tuple[bool, str]:
        """
        Valida il file prima del salvataggio
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Controllo dimensione
        if size > self.max_file_size:
            return False, f"File troppo grande. Massimo {self.max_file_size // 1024 // 1024}MB"
        
        if size == 0:
            return False, "File vuoto"
        
        # Controllo estensione
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return False, f"Estensione {file_ext} non consentita"
        
        # Controllo MIME type
        if content_type not in self.allowed_mime_types:
            # Prova a determinare il MIME type dal filename
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type and guessed_type in self.allowed_mime_types:
                # Se il tipo indovinato è valido, accetta il file
                return True, ""
            else:
                return False, f"Tipo file {content_type} non consentito"
        
        return True, ""
    
    def save_file(self, file_stream: BinaryIO, filename: str, content_type: str) -> Tuple[str, str, int, str]:
        """
        Salva file nel storage locale
        
        Args:
            file_stream: Stream del file
            filename: Nome originale del file
            content_type: MIME type del file
            
        Returns:
            Tuple[str, str, int, str]: (document_id, storage_path, size, file_hash)
        """
        try:
            # Genera ID univoco per il documento
            document_id = str(uuid.uuid4())
            
            # Crea directory per il documento
            doc_dir = self.base_path / document_id
            doc_dir.mkdir(exist_ok=True)
            
            # Path completo del file
            file_path = doc_dir / filename
            
            # Salva file e calcola hash
            file_hash = hashlib.sha256()
            size = 0
            
            with open(file_path, 'wb') as f:
                while True:
                    chunk = file_stream.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    file_hash.update(chunk)
                    size += len(chunk)
            
            return document_id, str(file_path), size, file_hash.hexdigest()
            
        except Exception as e:
            raise RuntimeError(f"Errore salvataggio file: {e}")
    
    def get_file_path(self, document_id: str, filename: str) -> Optional[Path]:
        """Ottieni il path del file dato l'ID documento"""
        file_path = self.base_path / document_id / filename
        
        if file_path.exists():
            return file_path
        return None
    
    def delete_file(self, document_id: str) -> bool:
        """Elimina file e directory del documento"""
        try:
            doc_dir = self.base_path / document_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)
                return True
            return False
        except Exception:
            return False
    
    def get_file_info(self, file_path: Path) -> dict:
        """Ottieni informazioni sul file"""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'mime_type': mime_type,
            'extension': file_path.suffix.lower()
        }
    
    def is_preview_supported(self, content_type: str) -> bool:
        """Verifica se il tipo di file supporta preview inline"""
        preview_types = {
            'application/pdf',
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp',
            'text/plain'
        }
        return content_type in preview_types

# Istanza globale del service
storage_service = StorageService()
