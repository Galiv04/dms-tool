#!/usr/bin/env python3
"""
Script avanzato per gestire utenti nel database DMS
- Lista utenti (test, non-test, tutti)
- Elimina utenti (test, singoli, multipli)
- Gestione interattiva e sicura
"""

import os
import sys
from pathlib import Path
import re

# Aggiungi il percorso della app al path Python
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.db.base import Base
    from app.db.models import User
except ImportError as e:
    print(f"❌ Errore di import: {e}")
    print("💡 Assicurati di essere nella directory backend/ e che il virtual environment sia attivo")
    sys.exit(1)

def get_database_url():
    """Determina l'URL del database usando lo stesso pattern dei test"""
    
    # Prova prima con variabile ambiente (come nei test)
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.endswith("test.db"):  # Evita DB di test
        return db_url
    
    # Path del database principale (come configurato nell'app)
    database_paths = [
        "./data/app.db",     # Path corretto che funziona
    ]
    
    for path in database_paths:
        full_path = Path(path).resolve()
        if full_path.exists():
            print(f"🔍 Trovato database: {full_path}")
            return f"sqlite:///{full_path}"
    
    # Se non trova nulla, usa il path standard dell'app
    app_db_path = backend_dir / "data" / "app.db"
    print(f"🔗 Usando path database: {app_db_path}")
    
    # Crea la directory se non esiste
    app_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return f"sqlite:///{app_db_path}"

def list_all_tables(session):
    """Lista tutte le tabelle disponibili nel database"""
    try:
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [row[0] for row in result]
        return tables
    except Exception as e:
        print(f"❌ Errore nel listare le tabelle: {e}")
        return []

def is_test_user(email):
    """Determina se un utente è di test basandosi sull'email"""
    test_patterns = [
        r'.*test.*@test\.com$',
        r'^api_user_.*@test\.com$',
        r'^test_docs_.*@example\.com$',
        r'^approver_.*@test\.com$',
        r'^manager_.*@test\.com$',
        r'^multiuser_.*@test\.com$',
        r'^other_.*@test\.com$',
        r'^contexttest_.*@test\.com$',
        r'^emptydocs_.*@test\.com$',
        r'.*_test_.*@.*$'
    ]
    
    for pattern in test_patterns:
        if re.match(pattern, email, re.IGNORECASE):
            return True
    return False

def get_database_session():
    """Crea e restituisce una sessione database"""
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine

def list_users(user_type="all"):
    """
    Lista utenti nel database
    user_type: 'all', 'test', 'normal'
    """
    
    print(f"🔗 Connessione database...")
    
    try:
        session, engine = get_database_session()
        
        # Verifica se la tabella users esiste
        tables = list_all_tables(session)
        if 'users' not in tables:
            print("❌ La tabella 'users' non esiste!")
            print("💡 Il database potrebbe non essere inizializzato.")
            return False
        
        # Query per ottenere tutti gli utenti
        query = text("""
            SELECT id, email, display_name, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        
        all_users = session.execute(query).fetchall()
        
        if not all_users:
            print("📭 Nessun utente trovato nel database.")
            return True
        
        # Filtra utenti in base al tipo richiesto
        filtered_users = []
        test_count = 0
        normal_count = 0
        
        for user in all_users:
            is_test = is_test_user(user[1])  # user[1] è l'email
            
            if is_test:
                test_count += 1
            else:
                normal_count += 1
            
            if user_type == "all":
                filtered_users.append((user, is_test))
            elif user_type == "test" and is_test:
                filtered_users.append((user, is_test))
            elif user_type == "normal" and not is_test:
                filtered_users.append((user, is_test))
        
        # Mostra statistiche
        print(f"\n📊 Statistiche utenti:")
        print(f"   👥 Totale: {len(all_users)}")
        print(f"   🧪 Test: {test_count}")
        print(f"   ✅ Normali: {normal_count}")
        
        # Mostra utenti filtrati
        if filtered_users:
            user_type_label = {
                "all": "tutti gli utenti",
                "test": "utenti di test", 
                "normal": "utenti normali"
            }
            
            print(f"\n📋 Lista {user_type_label[user_type]} ({len(filtered_users)}):")
            print("-" * 100)
            print(f"{'ID':<5} {'TIPO':<6} {'EMAIL':<45} {'NOME':<20} {'CREATO':<20}")
            print("-" * 100)
            
            for user, is_test in filtered_users:
                created_str = str(user[3])[:19] if user[3] else "N/A"
                name = (user[2] or 'N/A')[:19]
                email = user[1][:44]
                user_type_icon = "🧪" if is_test else "✅"
                
                print(f"{user[0]:<5} {user_type_icon:<6} {email:<45} {name:<20} {created_str:<20}")
        else:
            print(f"\n✅ Nessun utente del tipo '{user_type}' trovato!")
            
    except Exception as e:
        print(f"❌ Errore durante la ricerca: {e}")
        return False
        
    finally:
        try:
            session.close()
            engine.dispose()
        except:
            pass
    
    return True

def delete_test_users():
    """Elimina tutti gli utenti di test dal database"""
    
    print(f"🔗 Connessione database...")
    
    try:
        session, engine = get_database_session()
        
        # Verifica tabelle
        tables = list_all_tables(session)
        if 'users' not in tables:
            print("❌ La tabella 'users' non esiste!")
            return False
        
        # Prima conta gli utenti di test
        query = text("SELECT id, email FROM users ORDER BY email")
        all_users = session.execute(query).fetchall()
        
        test_users = [(user[0], user[1]) for user in all_users if is_test_user(user[1])]
        
        if not test_users:
            print("✅ Nessun utente di test trovato!")
            return True
        
        print(f"\n🧪 Trovati {len(test_users)} utenti di test da eliminare:")
        for user_id, email in test_users[:5]:  # Mostra solo i primi 5
            print(f"   • {email}")
        
        if len(test_users) > 5:
            print(f"   ... e altri {len(test_users) - 5} utenti")
        
        print(f"\n⚠️  ATTENZIONE: Verranno eliminati {len(test_users)} utenti di test!")
        print("   Questa operazione è IRREVERSIBILE!")
        
        confirm = input("\nDigita 'ELIMINA' per confermare: ")
        if confirm != 'ELIMINA':
            print("❌ Operazione annullata")
            return False
        
        # Elimina gli utenti di test
        deleted_count = 0
        for user_id, email in test_users:
            try:
                delete_query = text("DELETE FROM users WHERE id = :user_id")
                result = session.execute(delete_query, {"user_id": user_id})
                if result.rowcount > 0:
                    deleted_count += 1
                    print(f"❌ Eliminato: {email}")
            except Exception as e:
                print(f"⚠️  Errore eliminando {email}: {e}")
        
        # Commit
        session.commit()
        
        print(f"\n✅ Pulizia completata!")
        print(f"📊 Utenti eliminati: {deleted_count}/{len(test_users)}")
        
        # Conta rimanenti
        remaining_query = text("SELECT COUNT(*) FROM users")
        remaining_count = session.execute(remaining_query).scalar()
        print(f"👥 Utenti rimanenti: {remaining_count}")
        
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione: {e}")
        try:
            session.rollback()
        except:
            pass
        return False
        
    finally:
        try:
            session.close()
            engine.dispose()
        except:
            pass
    
    return True

def delete_user_by_email(email):
    """Elimina un singolo utente tramite email"""
    
    print(f"🔗 Connessione database...")
    
    try:
        session, engine = get_database_session()
        
        # Verifica se l'utente esiste
        query = text("SELECT id, email, display_name FROM users WHERE email = :email")
        user = session.execute(query, {"email": email}).fetchone()
        
        if not user:
            print(f"❌ Utente con email '{email}' non trovato!")
            return False
        
        print(f"\n👤 Utente trovato:")
        print(f"   ID: {user[0]}")
        print(f"   Email: {user[1]}")
        print(f"   Nome: {user[2] or 'N/A'}")
        print(f"   Tipo: {'🧪 Test' if is_test_user(user[1]) else '✅ Normale'}")
        
        print(f"\n⚠️  ATTENZIONE: Stai per eliminare l'utente '{email}'!")
        print("   Questa operazione è IRREVERSIBILE!")
        
        confirm = input(f"\nDigita 'ELIMINA' per confermare: ")
        if confirm != 'ELIMINA':
            print("❌ Operazione annullata")
            return False
        
        # Elimina l'utente
        delete_query = text("DELETE FROM users WHERE id = :user_id")
        result = session.execute(delete_query, {"user_id": user[0]})
        
        if result.rowcount > 0:
            session.commit()
            print(f"✅ Utente '{email}' eliminato con successo!")
        else:
            print(f"❌ Errore nell'eliminazione dell'utente")
            return False
        
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione: {e}")
        try:
            session.rollback()
        except:
            pass
        return False
        
    finally:
        try:
            session.close()
            engine.dispose()
        except:
            pass
    
    return True

def interactive_delete():
    """Modalità interattiva per eliminare utenti"""
    
    print("🎯 Modalità eliminazione interattiva")
    print("=" * 40)
    
    # Prima mostra tutti gli utenti
    if not list_users("all"):
        return False
    
    print("\n🎯 Opzioni di eliminazione:")
    print("1. Elimina tutti gli utenti di test")
    print("2. Elimina singolo utente per email")
    print("3. Annulla")
    
    choice = input("\nScegli un'opzione (1-3): ").strip()
    
    if choice == "1":
        return delete_test_users()
    elif choice == "2":
        email = input("\nInserisci l'email dell'utente da eliminare: ").strip()
        if not email:
            print("❌ Email non valida")
            return False
        return delete_user_by_email(email)
    elif choice == "3":
        print("❌ Operazione annullata")
        return True
    else:
        print("❌ Opzione non valida")
        return False

def show_database_info():
    """Mostra informazioni dettagliate sul database"""
    database_url = get_database_url()
    print(f"🔗 Database URL: {database_url}")
    
    # Estrai il path del file
    if database_url.startswith("sqlite:///"):
        db_file = database_url[10:]  # Rimuove "sqlite:///"
        db_path = Path(db_file)
        
        print(f"📁 Path file database: {db_path}")
        print(f"📂 Directory: {db_path.parent}")
        print(f"📄 Esiste: {'✅' if db_path.exists() else '❌'}")
        
        if db_path.exists():
            size = db_path.stat().st_size
            print(f"📏 Dimensione: {size} bytes ({size/1024:.1f} KB)")
            
            # Mostra anche statistiche utenti
            try:
                session, engine = get_database_session()
                
                # Conta utenti totali
                total_query = text("SELECT COUNT(*) FROM users")
                total_users = session.execute(total_query).scalar()
                
                # Conta utenti di test
                all_users_query = text("SELECT email FROM users")
                all_emails = session.execute(all_users_query).fetchall()
                test_users = sum(1 for email in all_emails if is_test_user(email[0]))
                normal_users = total_users - test_users
                
                print(f"\n📊 Statistiche utenti:")
                print(f"   👥 Totale: {total_users}")
                print(f"   🧪 Test: {test_users}")
                print(f"   ✅ Normali: {normal_users}")
                
                session.close()
                engine.dispose()
                
            except Exception as e:
                print(f"⚠️  Errore nel leggere statistiche: {e}")

def main():
    """Main function con tutte le opzioni"""
    print("🗃️  DMS User Management Script")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("📖 Utilizzo:")
        print("")
        print("📋 LISTA UTENTI:")
        print("  --list-all       # Lista tutti gli utenti")
        print("  --list-test      # Lista solo utenti di test")
        print("  --list-normal    # Lista solo utenti normali")
        print("")
        print("🗑️  ELIMINA UTENTI:")
        print("  --delete-test    # Elimina tutti gli utenti di test")
        print("  --delete-email <email>   # Elimina utente specifico")
        print("  --delete-interactive     # Modalità interattiva")
        print("")
        print("ℹ️  INFORMAZIONI:")
        print("  --info           # Info database")
        print("  --tables         # Lista tabelle")
        print("")
        print("Esempi:")
        print("  python db_interactive_cmds.py --list-test")
        print("  python db_interactive_cmds.py --delete-email user@test.com")
        print("  python db_interactive_cmds.py --delete-interactive")
        return
    
    command = sys.argv[1]
    
    # Lista utenti
    if command == "--list-all":
        list_users("all")
    elif command == "--list-test":
        list_users("test")
    elif command == "--list-normal":
        list_users("normal")
    
    # Elimina utenti
    elif command == "--delete-test":
        delete_test_users()
    elif command == "--delete-email":
        if len(sys.argv) < 3:
            print("❌ Specifica l'email dell'utente da eliminare")
            print("   Esempio: --delete-email user@test.com")
            return
        email = sys.argv[2]
        delete_user_by_email(email)
    elif command == "--delete-interactive":
        interactive_delete()
    
    # Informazioni
    elif command == "--info":
        show_database_info()
    elif command == "--tables":
        try:
            session, engine = get_database_session()
            tables = list_all_tables(session)
            print(f"📋 Tabelle nel database:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            if not tables:
                print("  Nessuna tabella trovata")
            session.close()
            engine.dispose()
        except Exception as e:
            print(f"❌ Errore: {e}")
    
    # Comandi legacy (per compatibilità)
    elif command == "--list":
        list_users("test")  # Comportamento legacy
    elif command == "--clean":
        delete_test_users()  # Comportamento legacy
    
    else:
        print(f"❌ Comando sconosciuto: {command}")
        print("💡 Usa senza parametri per vedere l'help completo")

if __name__ == "__main__":
    main()
