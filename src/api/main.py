from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .routes import router

app = FastAPI(
    title="API FitZone",
    description="Sistema de gestión de membresías, reservaciones y accesos para el gimnasio FitZone.",
    version="1.0.0",
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
