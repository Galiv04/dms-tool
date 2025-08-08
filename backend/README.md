# DMS Tool - Frontend React

Frontend React SPA per il sistema di gestione documenti con autenticazione e interfaccia utente responsive.

## 🚀 Quick Start

Installa dipendenze
    npm install

Avvia server di sviluppo
    npm run dev

Build per produzione
    npm run build

Preview build di produzione
    npm run preview

Applicazione disponibile su: http://localhost:5173

## 📋 Tecnologie

- **Framework**: React 18 con Vite
- **Routing**: React Router DOM
- **HTTP Client**: Axios con interceptors
- **State Management**: React Context API
- **Styling**: CSS puro con variabili CSS moderne
- **Build Tool**: Vite (veloce, moderno, zero-config)

## 🏗️ Architettura

    src/
    ├── App.jsx # Componente principale e routing
    ├── App.css # Stili globali e layout
    ├── main.jsx # Entry point React
    ├── api/
    │ ├── client.js # Axios client preconfigurato
    │ └── auth.js # API calls per autenticazione
    ├── components/
    │ ├── LoginForm.jsx # Form di login
    │ ├── RegisterForm.jsx # Form di registrazione
    │ └── ProtectedRoute.jsx # Route guard per aree protette
    └── context/
    └── AuthContext.jsx # Context per gestione stato auth


## 🔐 Gestione Autenticazione

### AuthContext
Gestione centralizzata dello stato di autenticazione:
- **Token storage**: localStorage per semplicità (futuro: cookie HttpOnly)
- **Auto-refresh**: Interceptors Axios per refresh automatico
- **Route protection**: Guard per rotte protette
- **Logout automatico**: Su errori 401

### Flusso Autenticazione
1. **Login** → Salva JWT in localStorage → Redirect a dashboard
2. **Requests** → Interceptor aggiunge automaticamente `Authorization: Bearer`
3. **401 Errors** → Auto-logout e redirect a login
4. **Logout** → Clear storage e redirect

### Componenti Autenticazione

#### LoginForm
- Validazione client-side
- Error handling con messaggi user-friendly
- Loading states durante richieste
- Link a registrazione

#### RegisterForm
- Validazione password (min 6 caratteri)
- Controllo email format
- Gestione errori (email già esistente, etc.)
- Feedback di successo

#### ProtectedRoute
- Wrapper per rotte che richiedono autenticazione
- Redirect automatico a `/login` se non autenticato
- Loading state durante verifica token

## 🎨 Styling e UX

### Layout Responsive
- **Header**: Info utente, logout, brand
- **Main Content**: Area principale con max-width centrata
- **Forms**: Styling consistente con focus states
- **Status Indicators**: Colori semantici (verde/rosso) per stati

### Design System

TBD


### Stati UI
- **Loading**: Indicatori durante operazioni async
- **Error**: Messaggi di errore contextual e chiari
- **Success**: Feedback positivo per azioni completate
- **Empty States**: Messaggi informativi quando non ci sono dati

## 🔧 Configurazione

### Variabili Ambiente

.env.local (opzionale)
    VITE_API_BASE_URL=http://localhost:8000
    VITE_APP_TITLE=DMS Tool

### API Client

// Configurazione base
const apiClient = axios.create({
baseURL: 'http://localhost:8000',
headers: { 'Content-Type': 'application/json' }
})

// Auto-inject JWT token
apiClient.interceptors.request.use(config => {
const token = localStorage.getItem('token')
if (token) {
config.headers.Authorization = Bearer ${token}
}
return config
})

## 📱 Routing Structure

    / (Home) # Dashboard principale (protected)
    ├── /login # Form di login
    ├── /register # Form di registrazione
    └── /health # Status check sistema (protected)

### Route Guards
- **ProtectedRoute**: Wrapper per rotte autenticate
- **Redirect Logic**: Auto-redirect a login se non autenticato
- **Public Routes**: Login e register accessibili senza auth

## 🧪 Testing (Future)

TBD

### Development

    npm run dev # Dev server con HMR
    npm run dev -- --host # Accessibile da network locale

### Production
    npm run build # Build ottimizzato
    npm run preview # Preview build locale

### Build Output
- **Assets**: Hashing automatico per cache busting
- **Code Splitting**: Bundle separati per vendor e app
- **Minification**: CSS e JS minificati
- **Source Maps**: Per debugging in produzione

## 📈 Prossimi Sviluppi (Roadmap)

### Fase 3 - Document Upload UI
- [ ] **Upload Component**: Drag & drop per file
- [ ] **Progress Indicators**: Barra progresso upload
- [ ] **File Validation**: Client-side validation (size, type)
- [ ] **Preview Component**: Anteprima PDF/immagini

### Fase 4 - Approval Workflow UI
- [ ] **Approval Dashboard**: Vista stato approvazioni
- [ ] **Document Viewer**: Visualizzatore documenti integrato
- [ ] **Notification System**: Toast notifications
- [ ] **Approval Actions**: Approva/Rifiuta con commenti

### Miglioramenti UX
- [ ] **Loading Skeletons**: Invece di spinner generici
- [ ] **Error Boundaries**: Gestione errori React graceful
- [ ] **Offline Support**: Service Worker per cache
- [ ] **PWA Features**: Installabile, push notifications

### Performance
- [ ] **React.lazy()**: Code splitting per pagine
- [ ] **React.memo()**: Ottimizzazione re-render
- [ ] **Virtual Scrolling**: Per liste lunghe
- [ ] **Image Optimization**: Lazy loading e responsive images

## 🔧 Development Tools

### Vite Configuration
    // vite.config.js
    export default {
    plugins: [react()],
    server: {
    port: 5173,
    proxy: {
    '/api': 'http://localhost:8000' // Proxy API calls
    }
    }
    }
