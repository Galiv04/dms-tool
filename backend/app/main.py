from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # Aggiungi questa riga
from app.routers import health, auth, documents
from app.config import settings

app = FastAPI(title=settings.app_name)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")  # Aggiungi questa riga

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["authentication"])  # Aggiungi auth
app.include_router(documents.router, tags=["documents"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}

# Aggiungi endpoint per favicon
@app.get("/favicon.ico")
async def favicon():
    return {"message": "Favicon not configured"}  # O redirect a /static/favicon.ico
