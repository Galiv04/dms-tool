import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from app.services.storage import StorageService

@pytest.fixture
def temp_storage():
    """Fixture per storage temporaneo con cleanup automatico garantito"""
    temp_dir = tempfile.mkdtemp()
    storage = StorageService(base_path=temp_dir)
    
    # Track dei file/directory creati durante i test
    created_items = []
    
    # Monkey patch del save_file per tracciare i file creati
    original_save_file = storage.save_file
    
    def tracked_save_file(*args, **kwargs):
        result = original_save_file(*args, **kwargs)
        if result:
            document_id, storage_path, size, file_hash = result
            created_items.append((document_id, storage_path))
        return result
    
    storage.save_file = tracked_save_file
    
    try:
        yield storage
    finally:
        # Cleanup garantito: rimuovi tutti i file tracciati
        for document_id, storage_path in created_items:
            try:
                if Path(storage_path).exists():
                    # Rimuovi il file specifico
                    Path(storage_path).unlink()
                
                # Rimuovi la directory del documento se vuota
                doc_dir = Path(storage_path).parent
                if doc_dir.exists() and not any(doc_dir.iterdir()):
                    doc_dir.rmdir()
            except Exception as e:
                print(f"⚠️ Warning cleanup file {storage_path}: {e}")
        
        # Cleanup finale: rimuovi tutta la directory temporanea
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleanup completato: {temp_dir}")
        except Exception as e:
            print(f"⚠️ Warning cleanup finale: {e}")

@pytest.mark.db
class TestStorageService:
    """Test per il servizio di storage con cleanup automatico"""
    
    def test_validate_file_success(self, temp_storage):
        """Test validazione file valido"""
        is_valid, message = temp_storage.validate_file("test.pdf", "application/pdf", 1024)
        assert is_valid is True
        assert message == ""
    
    def test_validate_file_too_large(self, temp_storage):
        """Test file troppo grande"""
        large_size = temp_storage.max_file_size + 1
        is_valid, message = temp_storage.validate_file("test.pdf", "application/pdf", large_size)
        assert is_valid is False
        assert "troppo grande" in message.lower()
    
    def test_validate_file_empty(self, temp_storage):
        """Test file vuoto"""
        is_valid, message = temp_storage.validate_file("test.pdf", "application/pdf", 0)
        assert is_valid is False
        assert "vuoto" in message.lower()
    
    def test_validate_file_wrong_extension(self, temp_storage):
        """Test estensione non consentita"""
        is_valid, message = temp_storage.validate_file("test.exe", "application/octet-stream", 1024)
        assert is_valid is False
        assert "estensione" in message.lower()
    
    def test_validate_file_wrong_mime_type(self, temp_storage):
        """Test MIME type non consentito"""
        is_valid, message = temp_storage.validate_file("test.pdf", "application/octet-stream", 1024)
        assert is_valid is True
        
        is_valid, message = temp_storage.validate_file("test.unknown", "application/octet-stream", 1024)
        assert is_valid is False
        assert ("estensione" in message.lower()) or ("tipo file" in message.lower())
    
    def test_save_file_success(self, temp_storage):
        """Test salvataggio file corretto"""
        test_content = b"Test PDF content"
        file_stream = BytesIO(test_content)
        
        document_id, storage_path, size, file_hash = temp_storage.save_file(
            file_stream, "test.pdf", "application/pdf"
        )
        
        assert document_id is not None
        assert len(document_id) == 36  # UUID format
        assert Path(storage_path).exists()
        assert size == len(test_content)
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA256 hex length
        
        # Il file verrà automaticamente pulito dalla fixture
    
    def test_get_file_path_exists(self, temp_storage):
        """Test recupero path file esistente"""
        test_content = b"Test content"
        file_stream = BytesIO(test_content)
        document_id, _, _, _ = temp_storage.save_file(file_stream, "test.pdf", "application/pdf")
        
        file_path = temp_storage.get_file_path(document_id, "test.pdf")
        assert file_path is not None
        assert file_path.exists()
    
    def test_get_file_path_not_exists(self, temp_storage):
        """Test recupero path file inesistente"""
        file_path = temp_storage.get_file_path("non-existent-id", "test.pdf")
        assert file_path is None
    
    def test_delete_file_success(self, temp_storage):
        """Test eliminazione file"""
        test_content = b"Test content"
        file_stream = BytesIO(test_content)
        document_id, storage_path, _, _ = temp_storage.save_file(file_stream, "test.pdf", "application/pdf")
        
        # Verifica che esista
        assert Path(storage_path).exists()
        
        # Elimina
        result = temp_storage.delete_file(document_id)
        assert result is True
        assert not Path(storage_path).exists()
    
    def test_delete_file_not_exists(self, temp_storage):
        """Test eliminazione file inesistente"""
        result = temp_storage.delete_file("non-existent-id")
        assert result is False
    
    def test_get_file_info(self, temp_storage):
        """Test informazioni file"""
        test_content = b"Test content"
        file_stream = BytesIO(test_content)
        document_id, storage_path, _, _ = temp_storage.save_file(file_stream, "test.pdf", "application/pdf")
        
        info = temp_storage.get_file_info(Path(storage_path))
        
        assert info['size'] == len(test_content)
        assert info['mime_type'] == 'application/pdf'
        assert info['extension'] == '.pdf'
        assert 'modified' in info
    
    def test_is_preview_supported(self, temp_storage):
        """Test supporto preview"""
        assert temp_storage.is_preview_supported('application/pdf') is True
        assert temp_storage.is_preview_supported('image/jpeg') is True
        assert temp_storage.is_preview_supported('text/plain') is True
        assert temp_storage.is_preview_supported('application/octet-stream') is False

# Test standalone con cleanup migliorato
def run_storage_tests():
    """Test standalone per storage service con cleanup garantito"""
    print("📄 Testing Storage Service...")
    print("=" * 50)
    
    # Setup temporaneo
    temp_dir = tempfile.mkdtemp()
    storage = StorageService(base_path=temp_dir)
    created_files = []
    
    try:
        print(f"🔧 Directory temporanea: {temp_dir}")
        
        print("\n1️⃣ Test validazione file...")
        is_valid, msg = storage.validate_file("test.pdf", "application/pdf", 1024)
        assert is_valid, f"Validazione fallita: {msg}"
        print("✅ Validazione file OK")
        
        print("\n2️⃣ Test salvataggio file...")
        test_content = b"Test PDF content for storage"
        file_stream = BytesIO(test_content)
        doc_id, path, size, hash_val = storage.save_file(file_stream, "test.pdf", "application/pdf")
        created_files.append((doc_id, path))
        
        assert len(doc_id) == 36, "Document ID non valido"
        assert Path(path).exists(), "File non salvato"
        assert size == len(test_content), "Dimensione file non corretta"
        print(f"✅ File salvato: {doc_id[:8]}.../{Path(path).name}")
        
        print("\n3️⃣ Test recupero file...")
        file_path = storage.get_file_path(doc_id, "test.pdf")
        assert file_path is not None, "File non trovato"
        assert file_path.exists(), "Path file non esiste"
        print(f"✅ File recuperato: {file_path}")
        
        print("\n4️⃣ Test informazioni file...")
        info = storage.get_file_info(file_path)
        assert info['size'] == len(test_content), "Info size errata"
        assert info['mime_type'] == 'application/pdf', "MIME type errato"
        print(f"✅ Info file: {info['size']} bytes, {info['mime_type']}")
        
        print("\n5️⃣ Test eliminazione file...")
        deleted = storage.delete_file(doc_id)
        assert deleted, "Eliminazione fallita"
        assert not Path(path).exists(), "File non eliminato"
        print("✅ File eliminato correttamente")
        
        print("\n🎉 Tutti i test storage completati!")
        return True
        
    except Exception as e:
        print(f"❌ Errore test storage: {e}")
        return False
    finally:
        # Cleanup garantito per standalone
        print(f"\n🧹 Pulizia directory temporanea...")
        
        # Rimuovi file rimasti
        for doc_id, file_path in created_files:
            try:
                if Path(file_path).exists():
                    Path(file_path).unlink()
                    print(f"🗑️ Rimosso: {Path(file_path).name}")
            except Exception as e:
                print(f"⚠️ Warning rimozione {file_path}: {e}")
        
        # Rimuovi directory temporanea
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                print(f"✅ Directory temporanea rimossa: {temp_dir}")
        except Exception as e:
            print(f"⚠️ Warning rimozione directory: {e}")

if __name__ == "__main__":
    run_storage_tests()
