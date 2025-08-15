# backend/testing/scripts/inspect_database.py
# Setup universale - funziona da qualsiasi directory!

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

from app.db.base import SessionLocal, engine
from app.db.models import User, Document, ApprovalRequest, ApprovalRecipient
from sqlalchemy import inspect, text
from datetime import datetime

def inspect_tables():
    """Ispeziona le tabelle e le colonne datetime nel database"""
    print("🗃️  ISPEZIONE DATABASE DMS")
    print("=" * 80)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Tabelle totali: {len(tables)}")
        print()
        
        # Lista tabelle
        print("📋 TABELLE ESISTENTI:")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        
        print("\n📅 COLONNE DATETIME PER TABELLA:")
        print("-" * 80)
        
        datetime_info = {}
        
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            
            # Trova colonne datetime
            dt_cols = []
            for col in columns:
                col_name, col_type = col['name'], str(col['type'])
                if (any(keyword in col_type.lower() for keyword in ['date', 'time']) or 
                    col_name.endswith('_at') or col_name.endswith('_on')):
                    dt_cols.append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': col['nullable']
                    })
            
            datetime_info[table_name] = dt_cols
            
            print(f"\n🏷️  {table_name.upper()}:")
            if dt_cols:
                for col in dt_cols:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"   ✅ {col['name']} ({col['type']}) - {nullable}")
            else:
                print("   ❌ Nessuna colonna datetime trovata")
        
        return datetime_info
        
    except Exception as e:
        print(f"❌ Errore durante l'ispezione: {e}")
        return {}

def show_sample_datetime_data():
    """Mostra dati di esempio per verificare i formati datetime"""
    print("\n🔍 DATI DATETIME DI ESEMPIO:")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Sample users
        users = db.query(User).limit(3).all()
        if users:
            print(f"\n👥 USERS (primi 3):")
            print(f"{'ID':<5} {'Email':<25} {'Created At':<25} {'Updated At':<25}")
            print("-" * 85)
            for user in users:
                created = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "N/A"
                updated = user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else "N/A"
                email = user.email[:22] + "..." if len(user.email) > 25 else user.email
                print(f"{user.id:<5} {email:<25} {created:<25} {updated:<25}")
        
        # Sample documents
        documents = db.query(Document).limit(3).all()
        if documents:
            print(f"\n📄 DOCUMENTS (primi 3):")
            print(f"{'ID':<5} {'Filename':<20} {'Created At':<25}")
            print("-" * 55)
            for doc in documents:
                created = doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else "N/A"
                filename = doc.filename[:17] + "..." if len(doc.filename) > 20 else doc.filename
                print(f"{doc.id:<5} {filename:<20} {created:<25}")
        
        # Sample approval requests
        approvals = db.query(ApprovalRequest).limit(3).all()
        if approvals:
            print(f"\n✅ APPROVAL_REQUESTS (primi 3):")
            print(f"{'ID':<5} {'Title':<15} {'Status':<12} {'Created At':<25}")
            print("-" * 65)
            for approval in approvals:
                created = approval.created_at.strftime("%Y-%m-%d %H:%M:%S") if approval.created_at else "N/A"
                title = approval.title[:12] + "..." if len(approval.title) > 15 else approval.title
                print(f"{approval.id:<5} {title:<15} {approval.status:<12} {created:<25}")
        
        # Sample approval recipients
        recipients = db.query(ApprovalRecipient).limit(3).all()
        if recipients:
            print(f"\n📧 APPROVAL_RECIPIENTS (primi 3):")
            print(f"{'ID':<5} {'Email':<20} {'Status':<12} {'Responded At':<25}")
            print("-" * 70)
            for recipient in recipients:
                responded = recipient.responded_at.strftime("%Y-%m-%d %H:%M:%S") if recipient.responded_at else "N/A"
                email = recipient.recipient_email[:17] + "..." if len(recipient.recipient_email) > 20 else recipient.recipient_email
                print(f"{recipient.id:<5} {email:<20} {recipient.status:<12} {responded:<25}")
        
    except Exception as e:
        print(f"❌ Errore nel recupero dati: {e}")
    finally:
        db.close()

def check_timezone_issues():
    """Verifica possibili problemi di timezone nei dati"""
    print("\n🌍 VERIFICA TIMEZONE:")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Controlla se i timestamp sono ragionevoli
        recent_users = db.query(User).filter(User.created_at.isnot(None)).limit(5).all()
        
        if recent_users:
            print("🕐 Analisi timestamp recenti:")
            now = datetime.now()
            
            for user in recent_users:
                if user.created_at:
                    diff = now - user.created_at.replace(tzinfo=None)
                    days_ago = diff.days
                    hours_ago = diff.seconds // 3600
                    
                    status = "✅ OK" if days_ago < 365 else "⚠️  Sospetto"
                    print(f"  {user.email[:25]:<25} | {user.created_at} | {days_ago}g {hours_ago}h fa | {status}")
            
            print(f"\n💡 Se vedi timestamp futuri o molto vecchi, potrebbero esserci problemi di timezone")
        else:
            print("📭 Nessun utente con timestamp da analizzare")
            
    except Exception as e:
        print(f"❌ Errore nella verifica timezone: {e}")
    finally:
        db.close()

def full_inspection():
    """Esegue un'ispezione completa del database"""
    datetime_info = inspect_tables()
    show_sample_datetime_data()
    check_timezone_issues()
    
    print(f"\n📋 RIASSUNTO ISPEZIONE:")
    print("=" * 80)
    
    total_datetime_cols = sum(len(cols) for cols in datetime_info.values())
    print(f"📊 Totale colonne datetime trovate: {total_datetime_cols}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Verifica che tutti i timestamp siano in formato corretto")
    print(f"2. Implementa le utility datetime_utils.py")  
    print(f"3. Aggiorna il frontend per usare timezone locale")
    print(f"4. Testa con dati reali")

if __name__ == "__main__":
    # Path setup solo per esecuzione standalone
    import sys, os
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    testing_dir = os.path.dirname(scripts_dir)
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # Parsing argomenti
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tables":
            inspect_tables()
        elif sys.argv[1] == "--samples":
            show_sample_datetime_data()
        elif sys.argv[1] == "--timezone":
            check_timezone_issues()
        else:
            print("❌ Argomento non riconosciuto")
            print("💡 Usa: --tables, --samples, --timezone o nessun argomento per ispezione completa")
    else:
        full_inspection()
    
    print("\n💡 Opzioni disponibili:")
    print("  python inspect_database.py          # Ispezione completa")
    print("  python inspect_database.py --tables # Solo struttura tabelle")
    print("  python inspect_database.py --samples # Solo dati di esempio")
    print("  python inspect_database.py --timezone # Solo verifica timezone")
