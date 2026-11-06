from enum import Enum
from typing import Dict, List
from .value_objects import EstadoDeReserva


class EstadoOperacion(Enum):
    SOLICITADA = "SOLICITADA"
    ACTIVA = "ACTIVA"
    SUSPENDIDA = "SUSPENDIDA"
    VENCIDA = "VENCIDA"
    CANCELADA = "CANCELADA"


class TransitionError(Exception):
    """Excepción de dominio lanzada cuando se intenta una transición inválida."""

    pass


class OperacionStateMachine:
    """
    Máquina de estados determinista para el ciclo de vida de las operaciones.
    Flujo base: SOLICITADA -> ACTIVA -> SUSPENDIDA -> VENCIDA
    Alternativa: SOLICITADA -> CANCELADA
    """

    TRANSICIONES_PERMITIDAS: Dict[EstadoOperacion, List[EstadoOperacion]] = {
        EstadoOperacion.SOLICITADA: [EstadoOperacion.ACTIVA, EstadoOperacion.CANCELADA],
        EstadoOperacion.ACTIVA: [EstadoOperacion.SUSPENDIDA, EstadoOperacion.VENCIDA],
        EstadoOperacion.SUSPENDIDA: [EstadoOperacion.ACTIVA, EstadoOperacion.VENCIDA],
        EstadoOperacion.VENCIDA: [],
        EstadoOperacion.CANCELADA: [],
    }

    def __init__(self, estado_inicial: EstadoOperacion = EstadoOperacion.SOLICITADA):
        self._estado_actual = estado_inicial

    @property
    def estado_actual(self) -> EstadoOperacion:
        return self._estado_actual

    def transicionar(self, nuevo_estado: EstadoOperacion) -> None:
        if nuevo_estado not in self.TRANSICIONES_PERMITIDAS[self._estado_actual]:
            raise TransitionError(
                f"Transición inválida: No se puede pasar de {self._estado_actual.value} a {nuevo_estado.value}"
            )
        self._estado_actual = nuevo_estado

    def activar(self):
        self.transicionar(EstadoOperacion.ACTIVA)

    def suspender(self):
        self.transicionar(EstadoOperacion.SUSPENDIDA)

    def vencer(self):
        self.transicionar(EstadoOperacion.VENCIDA)

    def cancelar(self):
        self.transicionar(EstadoOperacion.CANCELADA)
