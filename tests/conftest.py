import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.infrastructure.database import Base, get_db

# Importamos los modelos ORM explícitamente para que SQLAlchemy pueda crear las tablas
from src.infrastructure.orm import *
from src.api.main import app
from src.infrastructure.csv_loader import cargar_datos_iniciales

# Usamos StaticPool para obligar a SQLite a usar el mismo "archivero"
# en memoria para todas las peticiones de la prueba.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una base de datos nueva y limpia para cada prueba."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Inyectamos los datos del profesor (CSV) a nuestro modelo de gimnasio
    cargar_datos_iniciales(db)

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def cliente_api(db_session):
    """Simula a un recepcionista o socio usando nuestra API REST."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
