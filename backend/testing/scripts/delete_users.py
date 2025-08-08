# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

from app.db.base import SessionLocal
from app.db.models import User
from typing import List
import sys

def delete_users_by_emails(emails: List[str], dry_run: bool = True):
    """
    Elimina utenti dal database dato una lista di email
    
    Args:
        emails: Lista delle email degli utenti da eliminare
        dry_run: Se True, mostra solo cosa verrebbe eliminato senza fare modifiche
    """
    db = SessionLocal()
    
    try:
        print(f"🗑️  {'[DRY RUN] ' if dry_run else ''}Eliminazione utenti per email:")
        print("=" * 80)
        
        if not emails:
            print("📭 Nessuna email fornita")
            return 0
        
        # Trova gli utenti corrispondenti
        found_users = []
        not_found_emails = []
        
        for email in emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                found_users.append(user)
            else:
                not_found_emails.append(email)
        
        # Mostra risultati ricerca
        print(f"🔍 Email da cercare: {len(emails)}")
        print(f"✅ Utenti trovati: {len(found_users)}")
        print(f"❌ Email non trovate: {len(not_found_emails)}")
        print()
        
        # Lista utenti non trovati
        if not_found_emails:
            print("📭 Email non trovate nel database:")
            for email in not_found_emails:
                print(f"   ❌ {email}")
            print()
        
        # Lista utenti trovati
        if found_users:
            print("👥 Utenti che verranno eliminati:" if not dry_run else "👥 Utenti che sarebbero eliminati:")
            print(f"{'ID':<5} {'Email':<30} {'Nome':<20} {'Ruolo':<10}")
            print("-" * 65)
            
            for user in found_users:
                display_name = user.display_name or "N/A"
                print(f"{user.id:<5} {user.email:<30} {display_name:<20} {user.role.value:<10}")
            
            print("-" * 65)
        
        if not found_users:
            print("📭 Nessun utente da eliminare")
            return 0
        
        # Esegui eliminazione se non è dry run
        if not dry_run:
            print(f"\n🗑️  Procedendo con l'eliminazione di {len(found_users)} utenti...")
            
            deleted_count = 0
            for user in found_users:
                try:
                    print(f"   🗑️  Eliminando {user.email}...")
                    db.delete(user)
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Errore eliminando {user.email}: {e}")
            
            db.commit()
            print(f"\n✅ Eliminazione completata: {deleted_count}/{len(found_users)} utenti eliminati")
        else:
            print(f"\n💡 Questo è un DRY RUN. Usa --execute per eliminare realmente gli utenti")
        
        return len(found_users)
        
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def main():
    """Funzione principale con gestione argomenti"""
    if len(sys.argv) == 1:
        print("❌ Nessuna email fornita")
        print_usage()
        return
    
    # Parsing argomenti
    execute = False
    emails = []
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--execute":
            execute = True
        elif arg == "--emails":
            # Le email successive sono gli argomenti
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                emails.append(sys.argv[i])
                i += 1
            continue
        else:
            # Assume che sia una email
            emails.append(arg)
        i += 1
    
    if emails:
        delete_users_by_emails(emails, dry_run=not execute)
    else:
        print("❌ Nessuna email fornita")
        print_usage()

def print_usage():
    """Mostra come usare lo script"""
    print("\n📖 Uso dello script:")
    print("1. Dry run (visualizza senza eliminare):")
    print("   python delete_users.py user1@example.com user2@example.com")
    print()
    print("2. Eliminazione effettiva:")
    print("   python delete_users.py --execute user1@example.com user2@example.com")
    print()
    print("3. Con flag --emails:")
    print("   python delete_users.py --emails user1@example.com user2@example.com --execute")

if __name__ == "__main__":
        # Path setup solo per esecuzione standalone
    import sys, os
    testing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # La tua funzione standalone
    main()
