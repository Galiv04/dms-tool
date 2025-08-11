"""
Database Migration: Aggiunge campi necessari per Task Scheduler
=============================================================

Questa migration aggiunge:
1. Campo 'last_reminder_sent' alla tabella approval_recipients
2. Campo 'completion_notification_sent' alla tabella approval_requests

IMPORTANTE: Eseguire prima di avviare il Task Scheduler!
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

import sqlite3
from sqlalchemy import text, inspect
from app.db.base import engine
import sys
from datetime import datetime

def check_column_exists(table_name: str, column_name: str) -> bool:
    """
    Verifica se una colonna esiste già nella tabella
    
    Args:
        table_name: Nome della tabella
        column_name: Nome della colonna
        
    Returns:
        bool: True se la colonna esiste
    """
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        return column_name in column_names
    except Exception as e:
        print(f"⚠️ Error checking column {column_name} in {table_name}: {e}")
        # Fallback: prova a interrogare direttamente SQLite
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns_info = result.fetchall()
                column_names = [row[1] for row in columns_info]  # Nome colonna è il secondo campo
                return column_name in column_names
        except Exception as e2:
            print(f"⚠️ Fallback check also failed: {e2}")
            return False

def add_column_safe(conn, table_name: str, column_name: str, column_definition: str) -> bool:
    """
    Aggiunge una colonna in modo sicuro, controllando prima se esiste
    
    Args:
        conn: Connessione database
        table_name: Nome tabella
        column_name: Nome colonna da aggiungere
        column_definition: Definizione completa della colonna
        
    Returns:
        bool: True se operazione riuscita
    """
    try:
        if check_column_exists(table_name, column_name):
            print(f"   ⚠️ Column '{column_name}' already exists in '{table_name}' - skipping")
            return True
        
        # ✅ SQLite syntax corretto senza COMMENT
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
        print(f"   🔧 Executing: {sql}")
        
        conn.execute(text(sql))
        print(f"   ✅ Added '{column_name}' column successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error adding '{column_name}' to '{table_name}': {e}")
        return False

def upgrade():
    """Applica le modifiche al database (UP migration)"""
    
    print("🚀 Starting Task Scheduler Migration (SQLite Compatible)...")
    print("=" * 70)
    
    with engine.connect() as conn:
        migration_success = True
        
        # ✅ 1. Aggiungi campo last_reminder_sent (SENZA COMMENT)
        print("\n1️⃣ Adding 'last_reminder_sent' column to approval_recipients...")
        
        success1 = add_column_safe(
            conn, 
            'approval_recipients', 
            'last_reminder_sent',
            'last_reminder_sent DATETIME'  # ✅ Rimosso COMMENT e NULL (opzionale in SQLite)
        )
        
        if not success1:
            migration_success = False
        
        # ✅ 2. Aggiungi campo completion_notification_sent (SENZA COMMENT)
        print("\n2️⃣ Adding 'completion_notification_sent' column to approval_requests...")
        
        success2 = add_column_safe(
            conn,
            'approval_requests',
            'completion_notification_sent', 
            'completion_notification_sent DATETIME'  # ✅ Rimosso COMMENT e NULL
        )
        
        if not success2:
            migration_success = False
        
        # ✅ 3. Commit delle modifiche
        if migration_success:
            try:
                conn.commit()
                print("\n💾 Database changes committed successfully")
                
                # ✅ 4. Verifica finale
                print("\n🔍 Final Verification:")
                
                # Verifica approval_recipients
                reminder_exists = check_column_exists('approval_recipients', 'last_reminder_sent')
                print(f"   - last_reminder_sent in approval_recipients: {'✅' if reminder_exists else '❌'}")
                
                # Verifica approval_requests  
                notification_exists = check_column_exists('approval_requests', 'completion_notification_sent')
                print(f"   - completion_notification_sent in approval_requests: {'✅' if notification_exists else '❌'}")
                
                if reminder_exists and notification_exists:
                    print(f"\n🎉 Migration completed successfully at {datetime.now()}")
                    print("✅ Task Scheduler database schema is ready!")
                    return True
                else:
                    print(f"\n⚠️ Migration completed with warnings")
                    return False
                    
            except Exception as e:
                print(f"\n❌ Error committing changes: {e}")
                try:
                    conn.rollback()
                except:
                    pass
                return False
        else:
            print(f"\n❌ Migration failed - rolling back changes")
            try:
                conn.rollback()
            except:
                pass
            return False
    
    return True

def downgrade():
    """Rimuove le modifiche dal database (DOWN migration)"""
    
    print("🔄 Rolling back Task Scheduler Migration...")
    print("=" * 60)
    
    # ⚠️ IMPORTANTE: SQLite non supporta DROP COLUMN nativamente
    # Per rimuovere colonne serve ricreare la tabella
    print("⚠️ WARNING: SQLite does not support DROP COLUMN natively.")
    print("   To remove columns, tables would need to be recreated.")
    print("   This is a destructive operation and is not recommended.")
    print("   If you really need to remove these columns, do it manually.")
    
    return False  # Non implementiamo downgrade distruttivo

def status():
    """Mostra lo stato corrente della migration"""
    
    print("📊 Task Scheduler Migration Status")
    print("=" * 50)
    
    try:
        # Verifica connessione database
        with engine.connect() as conn:
            print("✅ Database connection: OK")
            
            # ✅ Verifica esistenza tabelle principali usando SQLite PRAGMA
            print(f"\n🔍 Checking tables and columns...")
            
            # Lista tabelle
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            required_tables = ['approval_recipients', 'approval_requests']
            
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}': EXISTS")
                    
                    # ✅ Verifica colonne usando PRAGMA table_info
                    result = conn.execute(text(f"PRAGMA table_info({table})"))
                    columns_info = result.fetchall()
                    column_names = [row[1] for row in columns_info]
                    
                    if table == 'approval_recipients':
                        has_reminder = 'last_reminder_sent' in column_names
                        print(f"   - last_reminder_sent: {'✅ EXISTS' if has_reminder else '❌ MISSING'}")
                    
                    elif table == 'approval_requests':  
                        has_notification = 'completion_notification_sent' in column_names
                        print(f"   - completion_notification_sent: {'✅ EXISTS' if has_notification else '❌ MISSING'}")
                        
                    # ✅ Mostra tutte le colonne per debug
                    print(f"     All columns: {', '.join(column_names)}")
                else:
                    print(f"❌ Table '{table}': MISSING")
            
            # ✅ Status generale
            reminder_ready = check_column_exists('approval_recipients', 'last_reminder_sent')
            notification_ready = check_column_exists('approval_requests', 'completion_notification_sent')
            
            print(f"\n📋 Migration Status:")
            if reminder_ready and notification_ready:
                print("✅ COMPLETE - Task Scheduler ready to run")
            elif reminder_ready or notification_ready:
                print("⚠️ PARTIAL - Some fields are missing")
                print("   Run: python migrations/add_scheduler_fields.py upgrade")
            else:
                print("❌ NOT APPLIED - Migration required")
                print("   Run: python migrations/add_scheduler_fields.py upgrade")
                
    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_migration():
    """Test della migration senza applicarla"""
    
    print("🧪 Testing Migration (Dry Run)")
    print("=" * 50)
    
    try:
        # Test connessione
        with engine.connect() as conn:
            print("✅ Database connection: OK")
            
            # Test check colonne esistenti
            tables_to_check = ['approval_recipients', 'approval_requests']
            
            for table in tables_to_check:
                try:
                    columns = check_column_exists(table, 'test_column_that_does_not_exist')
                    print(f"✅ Column check function works for {table}")
                except Exception as e:
                    print(f"❌ Column check failed for {table}: {e}")
                    return False
            
            # Test lettura schema
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='approval_recipients'"))
            schema = result.fetchone()
            if schema:
                print(f"✅ Can read table schema")
                print(f"   approval_recipients schema: {schema[0][:100]}...")
            else:
                print(f"❌ Cannot read table schema")
                return False
            
            print(f"\n✅ Migration test completed - ready to run upgrade")
            return True
            
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function per eseguire migration da comando"""
    
    if len(sys.argv) < 2:
        print("📖 Task Scheduler Database Migration (SQLite Compatible)")
        print("=" * 65)
        print()
        print("Usage:")
        print("  python add_scheduler_fields.py upgrade   # Applica migration")
        print("  python add_scheduler_fields.py status    # Mostra stato migration")
        print("  python add_scheduler_fields.py test      # Test migration (dry run)")
        print()
        print("⚠️ IMPORTANTE: Fare backup del database prima di eseguire upgrade!")
        print("⚠️ NOTA: Downgrade non supportato con SQLite per sicurezza")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "upgrade":
            success = upgrade()
            sys.exit(0 if success else 1)
            
        elif command == "status":
            success = status()
            sys.exit(0 if success else 1)
            
        elif command == "test":
            success = test_migration()
            sys.exit(0 if success else 1)
            
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: upgrade, status, test")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
