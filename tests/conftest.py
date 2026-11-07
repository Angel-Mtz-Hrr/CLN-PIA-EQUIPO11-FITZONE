import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.infrastructure.database import Base, get_db
from src.api.main import app
from src.infrastructure.csv_loader import cargar_datos_iniciales

# Creamos una base de datos temporal que solo vive en la memoria RAM
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
