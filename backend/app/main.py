from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config  # Garantiza la carga de variables y creación de UPLOAD_DIR
from app.routers import archivos, auth, dashboard, lineas, registros, reportes

app = FastAPI(
    title="API Sistema de Fondeo",
    description="Backend para el registro y monitoreo de progreso de líneas de fondeo en terreno",
    version="1.0.0",
)

# Configuración CORS para permitir peticiones desde el dashboard web y la app móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar en producción al dominio del dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Integración de todos los routers de la aplicación
app.include_router(auth.router)
app.include_router(lineas.router)
app.include_router(registros.router)
app.include_router(dashboard.router)
app.include_router(archivos.router)
app.include_router(reportes.router)


@app.get("/")
def health_check():
    return {
        "estado": "API operativa",
        "fase": "piloto SQLite",
        "upload_dir": config.UPLOAD_DIR,
    }