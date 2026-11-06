from abc import ABC, abstractmethod
from typing import Any


class Specification(ABC):
    """Interfaz base para el patrón Specification (DDD)."""

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        pass

    def __and__(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def __invert__(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.spec.is_satisfied_by(candidate)


# ==========================================
# Especificaciones Concretas (BR-05, BR-06, BR-07)
# ==========================================
class MembresiaVigenteSpec(Specification):
    """BR-06: Un socio con membresía vencida o suspendida no puede reservar."""

    def __init__(self, fecha_actual):
        self.fecha_actual = fecha_actual

    def is_satisfied_by(self, membresia: Any) -> bool:
        return membresia.esta_vigente_en(self.fecha_actual)


class ClaseIncluidaEnPlanSpec(Specification):
    """BR-07: Solo se pueden reservar clases incluidas en el plan."""

    def __init__(self, tipo_clase: str):
        self.tipo_clase = tipo_clase

    def is_satisfied_by(self, plan: Any) -> bool:
        return self.tipo_clase in plan.clases_incluidas


class CapacidadDisponibleSpec(Specification):
    """BR-05: Capacidad máxima definida (sin sobrecupo)."""

    def is_satisfied_by(self, clase_grupal: Any) -> bool:
        return clase_grupal.lugares_disponibles() > 0
