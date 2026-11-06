from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import Optional

# Importamos nuestros modelos de base de datos (archiveros)
from .orm import ClaseGrupalORM, MembresiaORM, PlanDeMembresiaORM
from src.domain.value_objects import ClaseId, SocioId


class ClaseGrupalRepository:
    """
    El encargado de buscar y guardar las Clases Grupales en la base de datos.
    Traduce el lenguaje de la base de datos (ORM) al lenguaje del negocio (Dominio).
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def obtener_por_id(self, clase_id: ClaseId) -> Optional[ClaseGrupalORM]:
        """Busca una clase específica, incluyendo quién está anotado y quién en lista de espera."""
        try:
            return (
                self.db.query(ClaseGrupalORM)
                .filter(ClaseGrupalORM.id == clase_id)
                .first()
            )
        except NoResultFound:
            return None

    def guardar(self, clase_orm: ClaseGrupalORM):
        """Guarda los cambios de una clase (ej. cuando alguien nuevo reserva)."""
        self.db.add(clase_orm)
        # Nota: La confirmación final (commit) se hace en la capa de aplicación,
        # así aseguramos que si algo falla, no se guarde información a medias.


class MembresiaRepository:
    """
    El encargado de revisar si un socio tiene su contrato (membresía) en regla.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def obtener_membresia_de_socio(self, socio_id: SocioId) -> Optional[MembresiaORM]:
        return (
            self.db.query(MembresiaORM)
            .filter(MembresiaORM.socio_id == socio_id)
            .first()
        )
