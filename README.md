# DMS Tool 📋

**Document Management System** con workflow di approvazione parallelo, autenticazione sicura e interfaccia moderna.

[![Status](https://img.shields.io/badge/Status-Phase%202%20Completed-success)](https://github.com/galiv04/dms-tool)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](./backend/)
[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB)](./frontend/)
[![Testing](https://img.shields.io/badge/Testing-pytest-blue)](./backend/testing/)

## ✨ Caratteristiche

### ✅ **Completate (Fase 1-2)**
- 🔐 **Autenticazione sicura** con JWT e Argon2id password hashing
- 👥 **Gestione utenti completa** con ruoli e permessi
- 🧪 **Testing framework robusto** (pytest + script standalone)
- 📱 **UI responsive** con React e context-based auth
- 🔧 **API RESTful** con documentazione automatica (OpenAPI/Swagger)

### 🚧 **In Sviluppo (Fase 3-4)**
- 📄 **Upload documenti** con validazione e preview
- ⚡ **Workflow approvazione parallelo** (ALL/ANY logic)
- 📧 **Sistema notifiche email** per approvazioni
- 📊 **Dashboard approvazioni** con stato real-time
- 🔍 **Document viewer** integrato

## 🚀 Quick Start
1. Clone repository
    git clone <your-repo-url>
    cd dms-tool

2. Setup backend
    cd backend
    python -m venv venv
    venv\Scripts\activate # Windows
    pip install -r requirements.txt
    alembic upgrade head

3. Setup frontend (nuovo terminale)
    cd frontend
    npm install

4. Start development
Terminal 1 - Backend
    uvicorn app.main:app --reload

Terminal 2 - Frontend
    npm run dev

5. Test everything
    cd backend/testing
    pytest -v

## More Info
- Backend: backend/README.md
- Frontend: frontend/README.md

## 🏗️ Architettura

    dms-tool/
    ├── 🖥️ backend/ # FastAPI REST API
    │ ├── app/ # Codice applicazione
    │ │ ├── routers/ # API endpoints
    │ │ ├── services/ # Business logic
    │ │ ├── db/ # Database & models
    │ │ └── utils/ # Utilities (JWT, hashing)
    │ ├── testing/ # Test framework completo
    │ │ ├── tests/ # Test automatizzati (pytest)
    │ │ └── scripts/ # Script gestione utenti
    │ └── data/ # Database SQLite
    ├── 🎨 frontend/ # React SPA
    │ ├── src/
    │ │ ├── components/ # UI components
    │ │ ├── context/ # State management
    │ │ └── api/ # HTTP client
    │ └── dist/ # Build di produzione
    └── 📋 docs/ # Documentazione (futuro)

## Database operations
    cd backend
    python ./testing/scripts/list_users.py # Lista utenti
    alembic current # Migration status

Clear state (reset)
    rm backend/data/app.db # Reset database
    rm -rf frontend/dist/ # Clear build

## 💻 Tecnologie

### Backend Stack
- **🚀 FastAPI** - Framework web moderno e veloce
- **🗄️ SQLAlchemy** - ORM con supporto async
- **🔐 Argon2id** - Password hashing sicuro (OWASP recommended)
- **🔑 JWT** - Token-based authentication
- **🧪 pytest** - Testing framework con fixtures
- **📊 Alembic** - Database migrations

### Frontend Stack  
- **⚛️ React 18** - UI library con hooks moderni
- **⚡ Vite** - Build tool veloce con HMR
- **🚦 React Router** - Client-side routing
- **📡 Axios** - HTTP client con interceptors
- **🎨 CSS3** - Styling moderno con custom properties

### Database & Storage
- **📱 SQLite** - Database per sviluppo (zero-config)
- **🐘 PostgreSQL** - Target per produzione
- **💾 Local Storage** - File storage (futuro: S3/MinIO)

## 🧪 Testing Strategy

### Livelli di Testing
1. **🔬 Unit Tests** - Logica business e utility
2. **🧬 Integration Tests** - API endpoints + database  
3. **🎭 E2E Tests** - Flussi completi user journey
4. **📋 Manual Tests** - Script interattivi per ops

### Coverage Attuale
Statistiche test (backend)
✅ Authentication: 95% coverage
✅ Database Models: 90% coverage
✅ User Management: 88% coverage
🚧 Document Upload: 0% (Fase 3)
🚧 Approval Workflow: 0% (Fase 4)

### Test Utils e Script
- **👥 User Management**: Lista, elimina, bulk operations
- **🔐 Auth Testing**: Registrazione, login, JWT validation
- **💾 Database Testing**: Models, migrations, cleanup

## 📊 Roadmap di Sviluppo

### 📍 **Fase 1 - Setup** ✅ *Completata*
- [x] Architettura progetto
- [x] Setup backend FastAPI
- [x] Setup frontend React
- [x] Database con SQLAlchemy

### 🔐 **Fase 2 - Autenticazione** ✅ *Completata*  
- [x] Sistema utenti sicuro (Argon2id)
- [x] JWT authentication
- [x] Frontend auth context
- [x] Testing framework completo

### 📄 **Fase 3 - Upload Documenti** 🚧 *Prossima*
- [ ] Service storage per file management
- [ ] API multipart upload con validazione
- [ ] Frontend upload UI (drag & drop)
- [ ] Document preview (PDF, immagini)
- [ ] Metadata e versioning

### ⚡ **Fase 4 - Workflow Approvazione** 🔮 *Pianificata*
- [ ] Approval engine (parallel/sequential)
- [ ] Email notifications system  
- [ ] Approval dashboard UI
- [ ] Token-based approval links
- [ ] Audit trail completo

### 🚀 **Fase 5 - Production Ready** 🔮 *Futura*
- [ ] Docker containerization
- [ ] CI/CD pipeline  
- [ ] Monitoring e logging
- [ ] Performance optimization
- [ ] Security hardening

## 🔒 Sicurezza e Compliance

### Implementazioni Attuali
- **🔐 Password Security**: Argon2id con parametri OWASP-compliant
- **🔑 JWT Security**: HS256 signing, scadenza configurabile
- **🛡️ Input Validation**: Pydantic V2 per validazione tipizzata
- **🚫 SQL Injection**: Protezione via SQLAlchemy ORM
- **📝 Audit Logging**: Tracking operazioni sensibili
- **🌐 CORS**: Configurato per frontend specifico

### Pianificate (Prossime Fasi)
- **📄 File Upload Security**: Scansione malware, type validation
- **🔗 Signed URLs**: Link temporanei per download sicuri  
- **👤 RBAC**: Role-based access control granulare
- **🔐 2FA**: Two-factor authentication (opzionale)
