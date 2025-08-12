# Document Management System (DMS)

Sistema di gestione documenti con workflow di approvazione avanzati, sviluppato in Python FastAPI + React.

## 🚀 Stato del Progetto

**✅ COMPLETATO:**
- Sistema di autenticazione completo (JWT)
- Upload e gestione documenti
- **✨ NUOVO: Sistema Approvazioni completo**
- **✨ NUOVO: Modal React per creazione richieste**
- **✨ NUOVO: Sistema notifiche toast**
- **✨ NUOVO: Tool gestione utenti avanzato**
- Database SQLite con migrazioni Alembic
- Test suite completa (103 test, coverage >95%)
- API RESTful documentate con OpenAPI/Swagger

**🔄 IN SVILUPPO:**
- Integrazione servizio email SMTP
- Gestione timezone e date
- Funzionalità eliminazione richieste
- Notifiche real-time WebSocket

## 🏗️ Architettura

dms-tool/
├── backend/ # FastAPI Backend
│ ├── app/
│ │ ├── api/ # Endpoints API
│ │ │ ├── auth.py # Autenticazione JWT
│ │ │ ├── documents.py # Gestione documenti
│ │ │ └── approvals.py # ✨ Sistema approvazioni
│ │ ├── core/ # Configurazione
│ │ ├── db/ # Database & Models
│ │ ├── services/ # Business Logic
│ │ │ ├── email.py # Servizio email (mock)
│ │ │ └── approval.py # ✨ Logica approvazioni
│ │ └── utils/ # Utilità
│ ├── testing/ # Test Suite
│ ├── data/ # Database SQLite
│ └── cleanup_test_users.py # ✨ Tool gestione utenti
├── frontend/ # React Frontend
│ ├── src/
│ │ ├── components/
│ │ │ ├── modals/ # ✨ Modal approvazioni
│ │ │ └── ui/ # Shadcn/ui components
│ │ ├── hooks/
│ │ │ └── useToast.js # ✨ Sistema notifiche
│ │ ├── pages/
│ │ │ └── ApprovalDashboard.jsx # ✨ Dashboard approvazioni
│ │ └── api/ # Client API
└── docs/ # Documentazione

text

## 🛠️ Tecnologie

**Backend:**
- **FastAPI** - Framework web moderno e veloce
- **SQLAlchemy** - ORM per database
- **Alembic** - Migrazioni database
- **JWT** - Autenticazione stateless
- **Pytest** - Testing framework
- **Pydantic** - Validazione dati

**Frontend:**
- **React 18** - UI framework
- **Vite** - Build tool
- **TanStack Query** - State management server
- **Shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **React Hook Form** - Form management
- **Zod** - Schema validation

## 🚀 Setup e Installazione

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git

### Backend Setup
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt

Setup database
alembic upgrade head

Run server
uvicorn app.main:app --reload --port 8000

text

### Frontend Setup
cd frontend
npm install
npm run dev # http://localhost:5173

text

## 🧪 Testing

### Backend Tests
cd backend
pytest -v # Tutti i test
pytest -m api # Solo test API
pytest -m db # Solo test database
pytest --cov=app # Con coverage

Test specifici
pytest testing/tests/test_approval_api.py -v

text

**Risultati Test:**
- ✅ **103 test passati**
- ✅ **Coverage >95%**
- ✅ **0 warnings**

### Frontend Tests
cd frontend
npm test # Jest tests
npm run test:e2e # Cypress E2E

text

## 🔑 Funzionalità Principali

### 1. **Sistema Autenticazione**
- Registrazione e login utenti
- JWT tokens con refresh
- Password hashing sicuro
- Middleware autenticazione

### 2. **Gestione Documenti**
- Upload file (PDF, DOC, XLS, etc.)
- Validazione tipo file e dimensione
- Storage sicuro con hash
- Download e preview
- Metadata e versioning

### 3. **✨ Sistema Approvazioni** (NUOVO)
- **Creazione richieste** con modal React responsive
- **Due tipi di approvazione**: "Tutti" o "Almeno uno"
- **Destinatari multipli**: utenti interni + email esterne
- **Validazione real-time** delle configurazioni
- **Dashboard completa** con filtri e statistiche
- **API RESTful** complete per CRUD operations

### 4. **✨ Sistema Notifiche** (NUOVO)
- **Toast notifications** per feedback utente
- **Varianti multiple**: success, error, warning, info
- **Auto-dismiss** configurabile
- **Posizionamento responsive**

## 📡 API Endpoints

### Autenticazione
POST /auth/register # Registrazione
POST /auth/login # Login
POST /auth/refresh # Refresh token

text

### Documenti
GET /documents/ # Lista documenti
POST /documents/upload # Upload file
GET /documents/{id} # Dettagli documento
DELETE /documents/{id} # Elimina documento
GET /documents/{id}/download # Download file

text

### ✨ Approvazioni (NUOVO)
GET /approvals/ # Lista richieste
POST /approvals/ # Crea richiesta
GET /approvals/{id} # Dettagli richiesta
POST /approvals/validate # Valida configurazione
GET /approvals/users # Utenti disponibili
GET /approvals/documents # Documenti per approvazione
GET /approvals/stats # Statistiche dashboard

text

## 🔧 Tool di Amministrazione

### ✨ Gestione Utenti (NUOVO)
Script Python avanzato per gestire utenti:

cd backend

Lista utenti
python cleanup_test_users.py --list-all # Tutti gli utenti
python cleanup_test_users.py --list-test # Solo utenti test
python cleanup_test_users.py --list-normal # Solo utenti normali

Elimina utenti
python cleanup_test_users.py --delete-test # Tutti gli utenti test
python cleanup_test_users.py --delete-email user@test.com # Utente specifico
python cleanup_test_users.py --delete-interactive # Modalità interattiva

Informazioni
python cleanup_test_users.py --info # Info database
python cleanup_test_users.py --tables # Lista tabelle

text

## 🗄️ Database Schema

### Tabelle Principali
- **users** - Utenti sistema
- **documents** - Documenti caricati
- **approval_requests** - ✨ Richieste di approvazione
- **approval_recipients** - ✨ Destinatari approvazioni

### Relazioni
users 1:N documents (owner)
users 1:N approval_requests (requester)
approval_requests 1:N approval_recipients
documents 1:N approval_requests

text

## 🌐 Interfaccia Utente

### Dashboard Principale
- Statistiche sistema
- Quick actions
- Stato servizi

### ✨ Dashboard Approvazioni (NUOVO)
- **Statistiche real-time**: totale, in attesa, approvate, rifiutate
- **Filtri avanzati**: per stato richiesta
- **Lista responsive**: con card dettagliate
- **Modal creazione**: workflow guidato step-by-step

### Gestione Documenti
- Upload drag & drop
- Lista con filtri
- Preview in-browser
- Download sicuro

## 🔒 Sicurezza

### Implementate
- ✅ **Autenticazione JWT** con expire
- ✅ **Password hashing** con bcrypt
- ✅ **Validazione input** con Pydantic
- ✅ **File type validation** per upload
- ✅ **SQL injection prevention** con SQLAlchemy ORM
- ✅ **CORS configurato** per frontend

### Best Practices
- Headers sicurezza HTTP
- Rate limiting API
- Input sanitization
- Error handling robusto

## 📊 Monitoring e Logging

- Structured logging con Python logging
- Error tracking e stack traces
- Performance monitoring API
- Database query monitoring

## 🚀 Deployment

### Sviluppo
Backend
cd backend && uvicorn app.main:app --reload

Frontend
cd frontend && npm run dev

text

### Produzione
Backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

Frontend
npm run build
serve -s dist

text

### Docker (Futuro)
docker-compose up --build

text

## 🛣️ Roadmap

### 🔄 Prossimi Step (Priorità Alta)
1. **📧 Integrazione Email SMTP**
   - Configurazione Gmail/SendGrid
   - Template email personalizzati
   - Tracking consegna

2. **⏰ Gestione Timezone**
   - Fix timestamp UTC/locale
   - Configurazione fuso orario utente
   - Date formatting consistente

3. **🗑️ Eliminazione Richieste**
   - Endpoint DELETE /approvals/{id}
   - Conferma eliminazione UI
   - Gestione stato "cancelled"

### 🔮 Funzionalità Future (Backlog)
- **Real-time notifications** con WebSocket
- **Advanced reporting** e analytics
- **Document versioning** avanzato
- **Bulk operations** per documenti
- **Role-based access control** granulare
- **API rate limiting** avanzato
- **Audit logging** completo
- **Multi-tenant** support
- **Mobile app** React Native
- **Desktop app** Electron

### 🏗️ Infrastruttura
- **Docker containerization**
- **CI/CD pipeline** GitHub Actions
- **Database backup** automatico
- **Performance monitoring**
- **Load balancing**

## 👥 Contribuzione

### Development Workflow
1. Fork del repository
2. Feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Pull Request

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ES6+, JSDoc comments
- **Testing**: >90% coverage richiesta
- **Commits**: Conventional commits format

## 📄 License

MIT License - vedi [LICENSE](LICENSE) file per dettagli.

## 🙏 Acknowledgments

- FastAPI team per l'excellent framework
- Shadcn per la UI component library
- React team per l'awesome frontend framework
- SQLAlchemy per l'ORM robusto

---

**🎯 Current Status: Sistema Approvazioni Completo**  
**📅 Last Updated: Agosto 2025**  