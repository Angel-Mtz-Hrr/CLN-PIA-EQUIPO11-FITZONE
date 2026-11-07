"""
Script para exportar el esquema OpenAPI oficial de FitZone a docs/api/openapi.json.
Útil para la documentación de entrega del PIA y validación de contratos Swagger UI.
"""

import json
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from src.api.main import app
except ModuleNotFoundError:
    # Soporte para entornos locales donde no se han instalado dependencias de persistencia
    import types

    mock_sa = types.ModuleType("sqlalchemy")
    mock_sa.__path__ = []
    mock_sa.create_engine = lambda *a, **k: None
    mock_sa.Column = lambda *a, **k: None
    mock_sa.String = lambda *a, **k: None
    mock_sa.Integer = lambda *a, **k: None
    mock_sa.DateTime = lambda *a, **k: None
    mock_sa.Boolean = lambda *a, **k: None
    mock_sa.ForeignKey = lambda *a, **k: None
    mock_sa.Enum = lambda *a, **k: None

    mock_orm = types.ModuleType("sqlalchemy.orm")
    mock_orm.__path__ = []

    class Session:
        pass

    class DeclarativeBase:
        def __init_subclass__(cls, **kwargs):
            pass

    mock_orm.Session = Session
    mock_orm.sessionmaker = lambda *a, **k: lambda: None
    mock_orm.declarative_base = lambda *a, **k: DeclarativeBase
    mock_orm.relationship = lambda *a, **k: None

    mock_exc = types.ModuleType("sqlalchemy.exc")

    class NoResultFound(Exception):
        pass

    mock_exc.NoResultFound = NoResultFound

    sys.modules["sqlalchemy"] = mock_sa
    sys.modules["sqlalchemy.orm"] = mock_orm
    sys.modules["sqlalchemy.exc"] = mock_exc

    from src.api.main import app


def export_openapi():
    output_path = os.path.join(BASE_DIR, "docs", "api", "openapi.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    openapi_data = app.openapi()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)

    print(f"Esquema OpenAPI exportado exitosamente a: {output_path}")


if __name__ == "__main__":
    export_openapi()
