import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Leemos la URL de la base de datos desde la configuración del sistema.
# Si el sistema no encuentra una ruta (por ejemplo, al ejecutar pruebas locales),
# usará un archivo local de SQLite temporal para no afectar los datos reales.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitzone_local.db")

# El "engine" es el motor que traduce nuestras instrucciones a lenguaje de base de datos.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# SessionLocal representa el "turno de trabajo" de un empleado.
# Cada vez que alguien hace una petición (ej. reservar), abrimos un turno, guardamos y cerramos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la plantilla de la cual heredarán todas nuestras tablas de datos.
Base = declarative_base()


def get_db():
    """
    Función que entrega una conexión segura a la base de datos.
    Asegura que el archivero se cierre correctamente al terminar, incluso si ocurre un error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
