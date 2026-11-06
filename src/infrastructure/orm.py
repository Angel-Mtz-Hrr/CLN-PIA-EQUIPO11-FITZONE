from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime

# Importamos el vocabulario oficial del negocio (nuestros Enums de Dominio)
from src.domain.value_objects import EstadoDeReserva, TipoRegistroHistorial
from .database import Base


class PlanDeMembresiaORM(Base):
    """
    Catálogo de planes que ofrece el gimnasio.
    Define qué clases están permitidas para el socio (BR-07).
    """

    __tablename__ = "planes_membresia"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)  # Ej. "Plan Básico", "Plan Premium"
    clases_incluidas = Column(String, nullable=False)  # Ej. "Yoga, Spinning, Box"


class MembresiaORM(Base):
    """
    El contrato actual de un socio.
    Recepción revisa esta ficha para confirmar si el socio tiene derecho a entrar (BR-06).
    """

    __tablename__ = "membresias"

    id = Column(String, primary_key=True, index=True)
    socio_id = Column(String, index=True, nullable=False)
    plan_id = Column(String, ForeignKey("planes_membresia.id"), nullable=False)

    inicio_vigencia = Column(DateTime, nullable=False)
    fin_vigencia = Column(DateTime, nullable=False)
    suspendida = Column(Boolean, default=False)


class ClaseGrupalORM(Base):
    """
    La agenda de una sesión física en el gimnasio.
    Guarda el cupo máximo definido por el Administrador para evitar sobrecupos (BR-05).
    """

    __tablename__ = "clases_grupales"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    capacidad_maxima = Column(Integer, nullable=False)

    # Si una clase se cancela o se borra, sus reservas y listas de espera asociadas se eliminan en cascada.
    reservas = relationship(
        "ReservaORM", back_populates="clase", cascade="all, delete-orphan"
    )
    lista_espera = relationship(
        "EntradaListaEsperaORM",
        back_populates="clase",
        cascade="all, delete-orphan",
        order_by="EntradaListaEsperaORM.posicion",
    )


class ReservaORM(Base):
    """
    El lugar apartado por un socio.
    Actúa como el pase de entrada que recepción verifica cuando el socio llega.
    """

    __tablename__ = "reservas"

    id = Column(String, primary_key=True, index=True)
    clase_id = Column(String, ForeignKey("clases_grupales.id"), nullable=False)
    socio_id = Column(String, index=True, nullable=False)

    # Forzamos que la base de datos solo acepte estados oficiales del negocio (ACTIVA, CANCELADA, etc.)
    estado = Column(
        SQLEnum(EstadoDeReserva), default=EstadoDeReserva.ACTIVA, nullable=False
    )
    fecha_creacion = Column(DateTime, default=datetime.now)

    clase = relationship("ClaseGrupalORM", back_populates="reservas")


class EntradaListaEsperaORM(Base):
    """
    La fila virtual cuando una clase está llena.
    Garantiza que el lugar se otorgue respetando el orden de llegada (US-05).
    """

    __tablename__ = "lista_espera"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clase_id = Column(String, ForeignKey("clases_grupales.id"), nullable=False)
    socio_id = Column(String, nullable=False)
    posicion = Column(Integer, nullable=False)
    fecha_ingreso = Column(DateTime, default=datetime.now)

    clase = relationship("ClaseGrupalORM", back_populates="lista_espera")


class RegistroHistorialORM(Base):
    """
    Bitácora histórica del comportamiento del socio.
    Ayuda al administrador a ver cuántas veces el socio reservó y no asistió (No-Shows).
    """

    __tablename__ = "historial_asistencia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    socio_id = Column(String, index=True, nullable=False)
    clase_id = Column(String, nullable=False)

    # Clasifica el evento (ASISTENCIA, CANCELACION, NO_SHOW)
    tipo_registro = Column(SQLEnum(TipoRegistroHistorial), nullable=False)
    instante = Column(DateTime, default=datetime.now)
