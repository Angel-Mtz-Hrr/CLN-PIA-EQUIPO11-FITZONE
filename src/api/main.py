import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .routes import router

from src.infrastructure.database import engine, Base, SessionLocal
from src.infrastructure.csv_loader import cargar_datos_iniciales
from src.infrastructure.orm import ClaseGrupalORM


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación:
    1. Asegura que las tablas existan en la base de datos (SQLite / PostgreSQL).
    2. Si la base de datos está vacía, puebla automáticamente los datos base de FitZone.
    """
    if os.getenv("ENVIRONMENT") != "testing":
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            if db.query(ClaseGrupalORM).count() == 0:
                cargar_datos_iniciales(db)
        except Exception as e:
            print(f"Aviso durante la inicialización de datos: {e}")
        finally:
            db.close()
    yield


tags_metadata = [
    {
        "name": "Gimnasio FitZone",
        "description": "Operaciones transaccionales y de consulta para clases, membresías y reservaciones.",
    },
]

app = FastAPI(
    title="API FitZone — Gestión de Gimnasio",
    description="""
Sistema RESTful de gestión de membresías, reservaciones de clases y control de acceso para el gimnasio **FitZone**.

### Arquitectura y Reglas del Dominio:
* **Invariante de Cupo (BR-05)**: Validación estricta para evitar sobrecupos en clases grupales.
* **Vigencia de Membresías (BR-06)**: Comprobación de suscripciones vigentes mediante Specifications.
* **Control de Acceso por Roles (BR-01 a BR-04)**: Autorización granular para Socios, Recepción e Instructores.
* **Manejo de Errores Empáticos**: Respuestas semánticas (HTTP 400 y 403) ante cualquier infracción de reglas de negocio.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 2,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "syntaxHighlight.theme": "monokai",
    },
)


# ==========================================
# MANEJADORES DE ERRORES EMPÁTICOS
# ==========================================
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Atrapa errores de reglas de negocio (ej. 'La clase está llena').
    Devuelve un Error 400 (Bad Request) con un mensaje claro en lugar de fallar catastróficamente.
    """
    return JSONResponse(
        status_code=400,
        content={
            "error": "Regla de Negocio",
            "mensaje": str(exc),
            "solucion": "Verifica los datos enviados o contacta a recepción.",
        },
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    """
    Atrapa errores de seguridad (ej. 'El instructor no puede cancelar clases').
    Devuelve un Error 403 (Forbidden).
    """
    return JSONResponse(
        status_code=403,
        content={
            "error": "Permiso Denegado",
            "mensaje": str(exc),
            "solucion": "No tienes el rol necesario para realizar esta acción.",
        },
    )


# Conectamos nuestras rutas a la aplicación principal
app.include_router(router, prefix="/api/v1")
