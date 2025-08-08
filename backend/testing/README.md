# DMS Tool - Testing Framework

Sistema di testing completo per il DMS Tool, che supporta sia **pytest** per test automatizzati che **script standalone** per operazioni manuali.

## 📁 Struttura dei File

    testing/
    ├── conftest.py # Configurazione pytest e fixtures
    ├── pytest.ini # Configurazione pytest
    ├── README.md # Questa documentazione
    ├── run_tests.py # Script principale per eseguire test
    ├── tests/ # Test automatizzati
    │ ├── init.py
    │ ├── setup_path.py # Configurazione path per test
    │ ├── test_db.py # Test database
    │ ├── test_auth.py # Test autenticazione
    │ └── test_user_management.py # Test gestione utenti
    └── scripts/ # Script funzionali
    ├── init.py
    ├── setup_path.py # Configurazione path per script
    ├── list_users.py # Lista utenti nel database
    ├── delete_users.py # Elimina utenti specifici
    └── bulk_delete_users.py # Eliminazione bulk utenti

## 🏷️ Categorie Test (Markers)

I test sono organizzati con **pytest markers**:

- **`@pytest.mark.db`** - Test del database
- **`@pytest.mark.auth`** - Test di autenticazione
- **`@pytest.mark.management`** - Test gestione utenti
- **`@pytest.mark.slow`** - Test che richiedono più tempo
- **`@pytest.mark.integration`** - Test di integrazione (richiedono backend attivo)

## 🚀 Come Eseguire i Test

#### Tutti i test

Dalla cartella backend/
    pytest

Con output verboso
    pytest -v

#### Per categoria

Solo test database
    pytest -m db

Solo test autenticazione
    pytest -m auth

Solo test gestione utenti
    pytest -m management

Escludi test lenti
    pytest -m "not slow"

Combinazioni
    pytest -m "db and not slow"

#### Test specifici

File specifico
    pytest ./testing/tests/test_db.py

Funzione specifica
    pytest ./testing/tests/test_db.py::test_database

Classe specifica
    pytest ./testing/tests/test_user_management.py::TestUserManagement

Test con pattern nel nome
    pytest -k "user"
    pytest -k "database or auth"

#### Con output e opzioni
Output molto verboso
    pytest -vv

Mostra output print anche se test passa
    pytest -s

Ferma al primo fallimento
    pytest -x

Report di coverage (se installato)
    pytest --cov=app

### Test Standalone (Con Output Console)

I test standalone mostrano output dettagliato e sono ideali per debug:

Dalla cartella backend/
    python ./testing/tests/test_db.py
    python ./testing/tests/test_auth.py
    python ./testing/tests/test_user_management.py
    
### Script Funzionali

#### Lista utenti
Lista semplice
    python ./testing/scripts/list_users.py

Lista dettagliata
    python ./testing/scripts/list_users.py --detailed

#### Eliminazione utenti specifici
Dry run (mostra cosa eliminerebbe)
    python ./testing/scripts/delete_users.py user1@test.com user2@test.com

Eliminazione effettiva
    python ./testing/scripts/delete_users.py --execute user1@test.com user2@test.com

#### Eliminazione bulk
Modalità interattiva
    python ./testing/scripts/bulk_delete_users.py

Elimina tutti (dry run)
    python ./testing/scripts/bulk_delete_users.py --all

Elimina tutti (effettivo)
    python ./testing/scripts/bulk_delete_users.py --all --execute

Elimina tutti eccetto alcuni
    python ./testing/scripts/bulk_delete_users.py --all --exclude admin@test.com --execute

Elimina da lista
    python ./testing/scripts/bulk_delete_users.py --list user1@test.com user2@test.com --execute


## 🔧 Configurazione e Setup

### Prerequisiti

Installa pytest se non presente
    pip install pytest pytest-asyncio

Assicurati che il backend sia nel venv
    cd backend
    ource venv/bin/activate # Linux/Mac

o
    venv\Scripts\activate # Windows


### Variabili d'ambiente

I test usano le stesse configurazioni del backend:
- Database: `sqlite:///./data/app.db`
- Secret key da `.env`

### Database di test

I test utilizzano lo stesso database del backend ma:
- Ogni test pulisce i dati che crea
- Usa transazioni e rollback quando possibile
- Test paralleli potrebbero richiedere database separati (configurazione futura)

## 📋 Checklist Pre-Push

Prima di fare push, esegui questa checklist:

1. Tutti i test passano
    pytest

2. Test specifici per area modificata
    pytest -m db # se hai modificato il database
    pytest -m auth # se hai modificato autenticazione
    pytest -m management # se hai modificato gestione utenti

3. Test di integrazione (se backend è attivo)
    pytest -m integration

4. Controllo rapido script
    python ./testing/scripts/list_users.py

