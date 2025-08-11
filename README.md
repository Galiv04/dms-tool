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
    ├── backend/ # FastAPI REST API
    │ ├── app/ # Core application
    │ ├── alembic/ # Database migrations
    │ └── README.md # Setup e API documentation
    ├── frontend/ # React SPA
    │ ├── src/ # Source code
    │ └── README.md # UI components e architecture

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
- **Celery + Redis** - Task queue e scheduling

### Frontend Stack  
- **React 18 + Vite** - UI framework e build tool
- **Shadcn/ui + Tailwind CSS** - Design system moderno
- **React Query** - State management server
- **React Hook Form** - Form management

### Database & Storage
- **📱 SQLite** - Database per sviluppo (zero-config)
- **🐘 PostgreSQL** - Target per produzione (TBD)
- **💾 Local Storage** - File storage (futuro: S3/MinIO)

## 🧪 Testing Strategy

### Livelli di Testing
1. **🔬 Unit Tests** - Logica business e utility
2. **🧬 Integration Tests** - API endpoints + database  
3. **🎭 E2E Tests** - Flussi completi user journey
4. **📋 Manual Tests** - Script interattivi per ops

## 📋 Roadmap di Sviluppo

### ✅ **Fasi 1-4: Sistema Core** - COMPLETATE
- [x] Architettura e autenticazione sicura
- [x] Upload/gestione documenti completa
- [x] Workflow approvazioni con email
- [x] Frontend moderno con Shadcn/ui
- [x] Task scheduler e dashboard

### 🎯 **Fase 5: Funzionalità Avanzate** - PROSSIMA
- [ ] **Sistema RBAC** - Ruoli e permessi granulari
- [ ] **Analytics & Reporting** - Dashboard statistiche avanzate
- [ ] **API Avanzate** - Bulk operations, search, versioning
- [ ] **Production Ready** - Docker, CI/CD, monitoring

### 🚀 **Fase 6: Enterprise Features** - FUTURA
- [ ] **Multi-tenant** - Organizzazioni separate
- [ ] **Integrations** - SSO, LDAP, external storage
- [ ] **Advanced Security** - 2FA, audit compliance
- [ ] **Mobile App** - React Native companion

## 🔒 Sicurezza

- **Password Hashing**: Argon2id (OWASP compliant)
- **API Security**: JWT tokens, input validation
- **File Security**: Type validation, secure storage
- **Audit Trail**: Logging completo operazioni

## 📚 Documentazione

- **Backend**: [Setup, API, Database](./backend/README.md)
- **Frontend**: [Components, Architecture, Styling](./frontend/README.md)
- **API Docs**: http://localhost:8000/docs (quando in esecuzione)


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
# DMS Tool - Document Management System

Sistema completo di gestione documentale con workflow di approvazione, autenticazione sicura e UI moderna.

## ✨ Funzionalità

- 🔐 **Autenticazione sicura** - JWT + Argon2id password hashing
- 📄 **Gestione documenti** - Upload drag & drop, preview, download sicuro
- ⚡ **Workflow approvazioni** - Parallelo/sequenziale con notifiche email
- 📊 **Dashboard moderne** - UI professionale con Shadcn/ui + Tailwind
- 🔔 **Sistema notifiche** - Real-time updates e scheduling automatico
- 📈 **Analytics** - Statistiche e audit trail completo

## 🚀 Quick Start

### Prerequisiti
```bash
# Verifica versioni
python --version  # 3.11+
node --version    # 20+


### Setup Completo
```bash
# 1. Clone e setup
git clone 
cd dms-tool

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000 &

# 3. Frontend (nuovo terminale)
cd frontend
npm install
npm run dev

# ✅ Accesso: http://localhost:5173
# ✅ API Docs: http://localhost:8000/docs
```

## 🏗️ Architettura

```
dms-tool/
├── backend/                    # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic  
│   │   ├── models/            # Database models
│   │   └── core/              # Config, security
│   ├── alembic/               # DB migrations
│   └── tests/                 # Test suite
├── frontend/                   # React + Shadcn/ui
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # React Query hooks
│   │   ├── pages/             # Route pages
│   │   └── api/               # API clients
│   └── dist/                  # Build output
└── README.md                  # This file
```

## 💻 Stack Tecnologico

**Backend**: FastAPI, PostgreSQL, SQLAlchemy, Celery, Redis, Argon2id, JWT  
**Frontend**: React 18, Vite, Shadcn/ui, Tailwind CSS v4, React Query, Lucide Icons  
**Tools**: Alembic, pytest, ESLint, Prettier

## 🔧 Backend

### Database
```bash
# Setup PostgreSQL
createdb dms_tool

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic current
alembic downgrade -1

# Reset database
alembic downgrade base
alembic upgrade head
```

### Development
```bash
cd backend

# Start server
uvicorn app.main:app --reload --port 8000

# With auto-reload and debug
uvicorn app.main:app --reload --log-level debug

# Production
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Environment
```bash
# .env file
cp .env.example .env

# Required variables
DATABASE_URL=postgresql://user:pass@localhost/dms_tool
SECRET_KEY=your-256-bit-secret-key
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Testing
```bash
cd backend

# Run all tests
pytest -v

# With coverage
pytest --cov=app tests/ --cov-report=html

# Specific test file
pytest tests/test_auth.py -v

# Test specific function
pytest tests/test_auth.py::test_register_user -v

# Fast fail
pytest -x

# Parallel execution
pytest -n auto
```

### API Endpoints
```bash
# Authentication
POST /auth/login              # Login user
POST /auth/register           # Register user  
GET  /auth/me                 # Current user

# Documents  
POST /documents/upload        # Upload file
GET  /documents/              # List documents
GET  /documents/{id}/download # Download file
DELETE /documents/{id}        # Delete document

# Approvals
POST /approvals/              # Create approval request
GET  /approvals/              # List approvals (filters: status)
POST /approvals/decide/{token}# Approve/reject via token
GET  /approvals/dashboard/stats # Dashboard statistics

# Admin
GET  /admin/scheduler/status  # Task scheduler status
POST /admin/scheduler/tasks/{id}/toggle # Enable/disable task
```

## 🎨 Frontend

### Development
```bash
cd frontend

# Development server
npm run dev
npm run dev -- --host        # Network accessible

# Build
npm run build
npm run preview              # Preview build

# Linting & Formatting
npm run lint
npm run format
```

### Shadcn/ui Components
```bash
# Setup Shadcn/ui
npx shadcn@latest init

# Add components
npx shadcn@latest add button card input alert
npx shadcn@latest add avatar badge separator progress
npx shadcn@latest add select dialog form label

# List available
npx shadcn@latest add
```

### Project Structure
```
src/
├── components/
│   ├── layout/               # AppLayout, Sidebar, TopNavbar
│   ├── ui/                   # Shadcn/ui components
│   ├── Documents.jsx         # Document management
│   ├── DocumentUpload.jsx    # Drag & drop upload
│   └── ApprovalDashboard.jsx # Approval workflow
├── hooks/
│   ├── useAuth.js           # Authentication
│   ├── useDocuments.js      # Document operations  
│   └── useApprovals.js      # Approval workflow
├── pages/                   # Route components
├── contexts/                # React contexts
└── api/                     # HTTP clients
```

### Routes
```
/                    # Dashboard overview
/documents          # Document management  
/approvals          # Approval workflow
/admin              # System administration
/login              # Authentication
/register           # User registration
```

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Full test suite
pytest tests/ -v

# Test categories
pytest tests/test_auth.py -v          # Authentication
pytest tests/test_documents.py -v     # Document upload/download
pytest tests/test_approvals.py -v     # Approval workflow
pytest tests/test_api.py -v           # API integration

# Coverage report
pytest --cov=app tests/ --cov-report=term-missing

# Performance tests
pytest tests/test_performance.py -v
```

### Frontend Tests (Future)
```bash
cd frontend

# Unit tests
npm test

# E2E tests  
npm run test:e2e

# Component tests
npm run test:components
```

## 📊 Database Operations

### User Management
```bash
cd backend

# List users
python -c "
from app.core.database import get_db
from app.models.user import User
db = next(get_db())
users = db.query(User).all()
for u in users: print(f'{u.id}: {u.email} - {u.display_name}')
"

# Create admin user
python -c "
from app.services.auth_service import AuthService
from app.core.database import get_db
auth = AuthService(next(get_db()))
user = auth.create_user('admin@example.com', 'password123', 'Admin User')
print(f'Created user: {user.email}')
"
```

### Database Inspection
```bash
# Connect to database
psql dms_tool

# List tables
\dt

# Describe table
\d users
\d documents
\d approval_requests

# Query examples
SELECT * FROM users;
SELECT * FROM documents WHERE uploaded_by = 1;
SELECT * FROM approval_requests WHERE status = 'pending';
```

## 🚀 Deployment

### Docker (Future)
```bash
# Build
docker build -t dms-backend backend/
docker build -t dms-frontend frontend/

# Run
docker-compose up -d
```

### Manual Production
```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
gunicorn app.main:app --workers 4

# Frontend  
cd frontend
npm run build
# Serve dist/ with nginx/apache
```

## 🔒 Security

### Password Security
- **Hashing**: Argon2id (OWASP compliant)
- **Parameters**: Memory 65536, iterations 3, parallelism 1
- **Validation**: Minimum 6 characters

### JWT Configuration
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
```

### File Upload Security
- **Validation**: File type, size limits
- **Storage**: Local filesystem (configurable)
- **Access Control**: User-based permissions

## 📈 Roadmap

### ✅ **Fasi 1-4 Completate**
- [x] Autenticazione JWT sicura
- [x] Upload/gestione documenti
- [x] Workflow approvazioni con email  
- [x] UI moderna Shadcn/ui + Tailwind
- [x] Task scheduler e notifiche
- [x] Dashboard e statistiche

### 🎯 **Fase 5: Funzionalità Avanzate**
- [ ] Sistema RBAC (ruoli e permessi)
- [ ] Analytics avanzate con grafici
- [ ] Bulk operations e search avanzata
- [ ] Real-time notifications (WebSocket)
- [ ] Document versioning

### 🚀 **Fase 6: Production Ready**  
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring e logging
- [ ] Performance optimization
- [ ] Security hardening

## 🆘 Troubleshooting

### Common Issues
```bash
# Port already in use
lsof -i :8000
kill -9 

# Database connection issues
psql -h localhost -U postgres -d dms_tool

# Frontend build issues
rm -rf node_modules package-lock.json
npm install

# Backend dependency issues
pip install --upgrade -r requirements.txt
```

### Logs
```bash
# Backend logs
tail -f logs/app.log

# Database logs  
tail -f /var/log/postgresql/postgresql.log

# Frontend dev logs
npm run dev | tee frontend.log
```

## 📚 Resources

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Database Schema**: Generated via Alembic migrations
- **Component Library**: [Shadcn/ui Documentation](https://ui.shadcn.com/)
- **Icons**: [Lucide Icons](https://lucide.dev/)

***

**Status**: ✅ Sistema completo e funzionale per gestione documenti enterprise con workflow di approvazione avanzato.

[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/66409374/b532076d-87b1-4e9e-a9e6-903b13294881/README.md
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/66409374/2bfbe455-fbf9-4ba9-bde3-cdceefb34226/README.md
[3] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/66409374/2212cc82-186c-405a-9fa9-5a9c0f893271/README.md