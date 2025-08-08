# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

from app.db.base import SessionLocal
from app.db.models import User
from typing import List, Optional
import sys

def delete_all_users(dry_run: bool = True, exclude_emails: Optional[List[str]] = None):
    """
    Elimina TUTTI gli utenti dal database
    
    Args:
        dry_run: Se True, mostra solo cosa verrebbe eliminato
        exclude_emails: Lista di email da NON eliminare
    """
    db = SessionLocal()
    
    try:
        print(f"⚠️  {'[DRY RUN] ' if dry_run else ''}ELIMINAZIONE DI TUTTI GLI UTENTI!")
        print("=" * 80)
        
        exclude_emails = exclude_emails or []
        
        # Query per tutti gli utenti
        query = db.query(User)
        if exclude_emails:
            query = query.filter(~User.email.in_(exclude_emails))
        
        users_to_delete = query.all()
        
        if not users_to_delete:
            print("📭 Nessun utente da eliminare")
            return 0
        
        print(f"🔍 Utenti totali da eliminare: {len(users_to_delete)}")
        
        if exclude_emails:
            print(f"🛡️  Email escluse dall'eliminazione: {len(exclude_emails)}")
            for email in exclude_emails:
                print(f"   🛡️  {email}")
            print()
        
        print("👥 Utenti che verranno eliminati:" if not dry_run else "👥 Utenti che sarebbero eliminati:")
        print(f"{'ID':<5} {'Email':<30} {'Nome':<20} {'Ruolo':<10}")
        print("-" * 65)
        
        for user in users_to_delete:
            display_name = user.display_name or "N/A"
            print(f"{user.id:<5} {user.email:<30} {display_name:<20} {user.role.value:<10}")
        
        print("-" * 65)
        
        if not dry_run:
            print(f"\n⚠️  ATTENZIONE: Stai per eliminare {len(users_to_delete)} utenti!")
            confirm = input("⚠️  Sei SICURO? Digita 'DELETE ALL' per confermare: ")
            
            if confirm != "DELETE ALL":
                print("❌ Eliminazione annullata (conferma non corretta)")
                return 0
            
            print(f"\n🗑️  Procedendo con l'eliminazione di {len(users_to_delete)} utenti...")
            
            deleted_count = 0
            for user in users_to_delete:
                try:
                    print(f"   🗑️  Eliminando {user.email}...")
                    db.delete(user)
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Errore eliminando {user.email}: {e}")
            
            db.commit()
            print(f"\n✅ Eliminazione completata: {deleted_count}/{len(users_to_delete)} utenti eliminati")
        else:
            print(f"\n💡 Questo è un DRY RUN. Usa --execute per eliminare realmente")
        
        return len(users_to_delete)
        
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def delete_users_from_list(user_list: List[str], dry_run: bool = True):
    """
    Elimina utenti da una lista fornita
    
    Args:
        user_list: Lista di email degli utenti da eliminare
        dry_run: Se True, mostra solo cosa verrebbe eliminato
    """
    db = SessionLocal()
    
    try:
        print(f"🗑️  {'[DRY RUN] ' if dry_run else ''}Eliminazione utenti da lista:")
        print("=" * 80)
        
        if not user_list:
            print("📭 Lista utenti vuota")
            return 0
        
        print(f"📋 Email nella lista: {len(user_list)}")
        for i, email in enumerate(user_list, 1):
            print(f"   {i}. {email}")
        print()
        
        # Trova gli utenti corrispondenti
        found_users = []
        not_found_emails = []
        
        for email in user_list:
            user = db.query(User).filter(User.email == email).first()
            if user:
                found_users.append(user)
            else:
                not_found_emails.append(email)
        
        print(f"✅ Utenti trovati: {len(found_users)}")
        print(f"❌ Email non trovate: {len(not_found_emails)}")
        
        if not_found_emails:
            print("\n📭 Email non trovate nel database:")
            for email in not_found_emails:
                print(f"   ❌ {email}")
        
        if not found_users:
            print("\n📭 Nessun utente da eliminare")
            return 0
        
        print(f"\n👥 Utenti da eliminare:")
        print(f"{'ID':<5} {'Email':<30} {'Nome':<20} {'Ruolo':<10}")
        print("-" * 65)
        
        for user in found_users:
            display_name = user.display_name or "N/A"
            print(f"{user.id:<5} {user.email:<30} {display_name:<20} {user.role.value:<10}")
        
        print("-" * 65)
        
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
            print(f"\n💡 Questo è un DRY RUN. Usa --execute per eliminare realmente")
        
        return len(found_users)
        
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def interactive_bulk_delete():
    """Modalità interattiva per eliminazione bulk"""
    print("🗑️  Eliminazione Bulk Utenti - Modalità Interattiva")
    print("=" * 60)
    print("1. Elimina TUTTI gli utenti")
    print("2. Elimina da lista fornita")
    print("3. Elimina tutti ECCETTO alcuni")
    print("4. Esci")
    print("=" * 60)
    
    choice = input("Scegli un'opzione (1-4): ").strip()
    
    if choice == "1":
        print("\n⚠️  ATTENZIONE: Eliminerai TUTTI gli utenti!")
        confirm = input("Vuoi continuare? (yes/no): ").lower()
        if confirm in ['yes', 'y']:
            # Prima dry run
            delete_all_users(dry_run=True)
            final_confirm = input("\nProcedere con l'eliminazione effettiva? (yes/no): ").lower()
            if final_confirm in ['yes', 'y']:
                delete_all_users(dry_run=False)
            else:
                print("❌ Eliminazione annullata")
        else:
            print("❌ Operazione annullata")
    
    elif choice == "2":
        print("\n📧 Inserisci le email degli utenti da eliminare (una per riga)")
        print("💡 Premi Enter su riga vuota per terminare")
        
        emails = []
        while True:
            email = input("Email: ").strip()
            if not email:
                break
            emails.append(email)
        
        if emails:
            # Prima dry run
            delete_users_from_list(emails, dry_run=True)
            confirm = input("\nProcedere con l'eliminazione? (yes/no): ").lower()
            if confirm in ['yes', 'y']:
                delete_users_from_list(emails, dry_run=False)
            else:
                print("❌ Eliminazione annullata")
        else:
            print("📭 Nessuna email inserita")
    
    elif choice == "3":
        print("\n🛡️  Inserisci le email da PRESERVARE (una per riga)")
        print("💡 Premi Enter su riga vuota per terminare")
        
        exclude_emails = []
        while True:
            email = input("Email da preservare: ").strip()
            if not email:
                break
            exclude_emails.append(email)
        
        # Prima dry run
        delete_all_users(dry_run=True, exclude_emails=exclude_emails)
        confirm = input("\nProcedere con l'eliminazione? (yes/no): ").lower()
        if confirm in ['yes', 'y']:
            delete_all_users(dry_run=False, exclude_emails=exclude_emails)
        else:
            print("❌ Eliminazione annullata")
    
    elif choice == "4":
        print("👋 Uscita")
    else:
        print("❌ Opzione non valida")

def main():
    """Funzione principale"""
    if len(sys.argv) == 1:
        # Modalità interattiva
        interactive_bulk_delete()
        return
    
    # Parsing argomenti
    if "--all" in sys.argv:
        execute = "--execute" in sys.argv
        exclude_emails = []
        
        # Cerca email da escludere
        if "--exclude" in sys.argv:
            exclude_idx = sys.argv.index("--exclude")
            exclude_emails = sys.argv[exclude_idx + 1:]
        
        delete_all_users(dry_run=not execute, exclude_emails=exclude_emails)
    
    elif "--list" in sys.argv:
        execute = "--execute" in sys.argv
        
        # Leggi lista da file o argomenti
        emails = []
        if "--file" in sys.argv:
            file_idx = sys.argv.index("--file")
            if file_idx + 1 < len(sys.argv):
                filename = sys.argv[file_idx + 1]
                try:
                    with open(filename, 'r') as f:
                        emails = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    print(f"❌ File {filename} non trovato")
                    return
        else:
            # Email da argomenti
            emails = [arg for arg in sys.argv if "@" in arg]
        
        delete_users_from_list(emails, dry_run=not execute)
    
    else:
        print_usage()

def print_usage():
    """Mostra come usare lo script"""
    print("\n📖 Uso dello script:")
    print("1. Modalità interattiva:")
    print("   python bulk_delete_users.py")
    print()
    print("2. Elimina tutti gli utenti (dry run):")
    print("   python bulk_delete_users.py --all")
    print()
    print("3. Elimina tutti gli utenti (effettivo):")
    print("   python bulk_delete_users.py --all --execute")
    print()
    print("4. Elimina tutti eccetto alcuni:")
    print("   python bulk_delete_users.py --all --exclude admin@test.com user@test.com --execute")
    print()
    print("5. Elimina da lista:")
    print("   python bulk_delete_users.py --list user1@test.com user2@test.com --execute")
    print()
    print("6. Elimina da file:")
    print("   python bulk_delete_users.py --list --file users_to_delete.txt --execute")

if __name__ == "__main__":
    # Path setup solo per esecuzione standalone
    import sys, os
    testing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # La tua funzione standalone
    main()
