# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

from app.db.base import SessionLocal
from app.db.models import User
from datetime import datetime

def list_all_users():
    """Lista tutti gli utenti presenti nel database"""
    db = SessionLocal()
    
    try:
        print("👥 Lista utenti nel database:")
        print("=" * 80)
        
        users = db.query(User).order_by(User.created_at).all()
        
        if not users:
            print("📭 Nessun utente trovato nel database")
            return []
        
        print(f"📊 Totale utenti: {len(users)}")
        print()
        
        # Header della tabella
        print(f"{'ID':<5} {'Email':<30} {'Nome':<20} {'Ruolo':<10} {'Creato':<20}")
        print("-" * 85)
        
        for user in users:
            created_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "N/A"
            display_name = user.display_name or "N/A"
            
            print(f"{user.id:<5} {user.email:<30} {display_name:<20} {user.role.value:<10} {created_str:<20}")
        
        print("-" * 85)
        print(f"📋 Lista completata - {len(users)} utenti trovati")
        
        return users
        
    except Exception as e:
        print(f"❌ Errore durante il recupero degli utenti: {e}")
        return []
    finally:
        db.close()

def list_users_detailed():
    """Lista utenti con dettagli aggiuntivi"""
    db = SessionLocal()
    
    try:
        print("👥 Lista dettagliata utenti:")
        print("=" * 80)
        
        users = db.query(User).order_by(User.created_at).all()
        
        if not users:
            print("📭 Nessun utente trovato nel database")
            return []
        
        for i, user in enumerate(users, 1):
            print(f"\n{i}. Utente #{user.id}")
            print(f"   📧 Email: {user.email}")
            print(f"   👤 Nome: {user.display_name or 'Non specificato'}")
            print(f"   🔒 Ruolo: {user.role.value}")
            print(f"   📅 Creato: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
            print(f"   🔄 Aggiornato: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'N/A'}")
            
            # Conta documenti e approvazioni (quando li implementeremo)
            print(f"   📄 Documenti: 0")  # TODO: implementare quando avremo i documenti
            print(f"   ✅ Richieste approvazione: 0")  # TODO: implementare
        
        print(f"\n📋 Totale: {len(users)} utenti")
        
        return users
        
    except Exception as e:
        print(f"❌ Errore durante il recupero degli utenti: {e}")
        return []
    finally:
        db.close()

if __name__ == "__main__":
    # Path setup solo per esecuzione standalone
    import sys, os
    testing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # La tua funzione standalone
    
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        list_users_detailed()
    else:
        list_all_users()
    
    print("\n💡 Usa 'python list_users.py --detailed' per vista dettagliata")
