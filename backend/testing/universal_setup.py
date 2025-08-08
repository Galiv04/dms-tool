"""
Setup universale che funziona da qualsiasi directory
"""
import sys
import os

def find_backend_dir():
    """Trova la directory backend partendo da qualsiasi punto"""
    current = os.path.abspath(os.getcwd())
    
    # Controlla se siamo già in backend
    if os.path.exists(os.path.join(current, 'app', 'main.py')):
        return current
    
    # Cerca backend andando in su
    path = current
    for _ in range(5):  # Max 5 livelli su
        path = os.path.dirname(path)
        if os.path.exists(os.path.join(path, 'app', 'main.py')):
            return path
    
    # Ultima risorsa: guarda nei subdirectory
    for root, dirs, files in os.walk(current):
        if 'main.py' in files and 'app' in os.path.basename(os.path.dirname(root)):
            return os.path.dirname(root)
    
    raise RuntimeError("Impossibile trovare la directory backend")

def setup_backend_path():
    """Setup automatico del path backend"""
    try:
        backend_dir = find_backend_dir()
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        return backend_dir
    except RuntimeError as e:
        print(f"❌ Errore setup path: {e}")
        return None

# Setup automatico
BACKEND_DIR = setup_backend_path()
