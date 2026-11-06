from dataclasses import dataclass, field
from datetime import datetime


class DomainEvent:
    """Clase base para todos los eventos del negocio."""

    pass


@dataclass(frozen=True)
class ReservaRealizada(DomainEvent):
    clase_id: str
    socio_id: str
    fecha_ocurrencia: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ReservaCancelada(DomainEvent):
    clase_id: str
    socio_id: str
    fecha_ocurrencia: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class LugarOfrecidoASocio(DomainEvent):
    clase_id: str
    socio_id: str
    fecha_ocurrencia: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class AsistenciaRegistrada(DomainEvent):
    clase_id: str
    socio_id: str
    fecha_ocurrencia: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class NoShowRegistrado(DomainEvent):
    clase_id: str
    socio_id: str
    fecha_ocurrencia: datetime = field(default_factory=datetime.now)
