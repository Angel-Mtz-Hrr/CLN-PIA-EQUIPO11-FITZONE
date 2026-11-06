from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from typing import NewType, Optional

# ==========================================
# CORE TYPES (IDs Tipados)
# Evitan que mezclemos accidentalmente un ID de Socio con un ID de Clase.
# ==========================================
SocioId = NewType("SocioId", str)
ClaseId = NewType("ClaseId", str)
ReservaId = NewType("ReservaId", str)
MembresiaId = NewType("MembresiaId", str)
PlanId = NewType("PlanId", str)
InstructorId = NewType("InstructorId", str)
AvisoId = NewType("AvisoId", str)


# ==========================================
# ENUMERACIONES (Máquinas de Estado y Categorías)
# ==========================================
class Rol(Enum):
    SOCIO = "Socio"
    RECEPCION = "Recepción"
    INSTRUCTOR = "Instructor"
    ADMINISTRADOR = "Administrador"
    SISTEMA = "Sistema"


class EstadoDeReserva(Enum):
    SOLICITADA = "SOLICITADA"
    ACTIVA = "ACTIVA"
    CANCELADA = "CANCELADA"
    ASISTIDA = "ASISTIDA"
    NO_SHOW = "NO_SHOW"


class EstadoEntradaListaEspera(Enum):
    ESPERANDO = "Esperando"
    OFERTADA = "Ofertada"
    CONFIRMADA = "Confirmada"
    EXPIRADA = "Expirada"


class MotivoRechazo(Enum):
    MEMBRESIA_NO_VIGENTE = "MEMBRESIA_NO_VIGENTE"
    CLASE_FUERA_DEL_PLAN = "CLASE_FUERA_DEL_PLAN"
    CUPO_LLENO = "CUPO_LLENO"
    RESERVA_NO_ENCONTRADA = "RESERVA_NO_ENCONTRADA"


class TipoRegistroHistorial(Enum):
    ASISTENCIA = "Asistencia"
    CANCELACION = "Cancelación"
    NO_SHOW = "No-Show"


# ==========================================
# VALUE OBJECTS (Inmutables con validación)
# ==========================================
@dataclass(frozen=True)
class Actor:
    """Modela quién ejecuta la acción (BR-01, BR-02, BR-03, BR-04)"""

    id: str
    rol: Rol


@dataclass(frozen=True)
class Capacidad:
    """Protege la invariante de que el cupo nunca sea negativo (BR-05)"""

    valor: int

    def __post_init__(self):
        if self.valor <= 0:
            raise ValueError("La capacidad debe ser un entero mayor que cero.")


@dataclass(frozen=True)
class Horario:
    """Asegura la coherencia temporal de una sesión"""

    inicio: datetime
    fin: datetime

    def __post_init__(self):
        if self.inicio >= self.fin:
            raise ValueError(
                "El inicio del horario debe ser estrictamente anterior al fin."
            )


@dataclass(frozen=True)
class VigenciaDeMembresia:
    """Permite calcular dinámicamente si un acceso o reserva es válido (BR-06)"""

    inicio: datetime
    vencimiento: datetime

    def esta_vigente_en(self, instante: datetime) -> bool:
        return self.inicio <= instante <= self.vencimiento


@dataclass(frozen=True)
class PosicionEnLista:
    """Protege el orden de llegada en la lista de espera (US-05)"""

    valor: int

    def __post_init__(self):
        if self.valor <= 0:
            raise ValueError("La posición en lista debe ser un entero positivo.")


@dataclass(frozen=True)
class VentanaDeConfirmacion:
    """Tiempo configurable para confirmar una oferta de la lista de espera (SP-02)"""

    duracion: timedelta


# ==========================================
# OBJETOS DE RESULTADO (Comunicación de Reglas)
# ==========================================
@dataclass(frozen=True)
class ResultadoDeElegibilidad:
    es_elegible: bool
    motivo_rechazo: Optional[MotivoRechazo] = None

    @classmethod
    def aprobado(cls) -> "ResultadoDeElegibilidad":
        return cls(es_elegible=True)

    @classmethod
    def rechazado(cls, motivo: MotivoRechazo) -> "ResultadoDeElegibilidad":
        return cls(es_elegible=False, motivo_rechazo=motivo)


@dataclass(frozen=True)
class ResultadoDeAcceso:
    acceso_permitido: bool
    motivo_rechazo: Optional[str] = None
