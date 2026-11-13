"""
Pruebas UNITARIAS de las reglas de negocio corregidas (BR-03, BR-07, BR-08, BR-09).
No usan base de datos ni API: prueban el dominio puro.
"""
import pytest
from datetime import datetime, timedelta

from src.domain.entities import ClaseGrupal, PlanDeMembresia
from src.domain.value_objects import (
    ClaseId,
    SocioId,
    ReservaId,
    Capacidad,
    Horario,
    Actor,
    Rol,
    PlanId,
    EstadoDeReserva,
)
from src.domain.specifications import ClaseIncluidaEnPlanSpec


# ---------- Ayudantes ----------
def crear_clase(inicio=None, fin=None, capacidad=5):
    """Crea una clase de prueba. Por defecto empieza ahora y dura 1 hora."""
    inicio = inicio or datetime.now()
    fin = fin or inicio + timedelta(hours=1)
    return ClaseGrupal(
        id=ClaseId("FIT-P001"),
        nombre="Clase Mensual 01",
        horario=Horario(inicio=inicio, fin=fin),
        capacidad=Capacidad(capacidad),
    )


SOCIO_1 = Actor(id="FIT-C001", rol=Rol.SOCIO)
SOCIO_2 = Actor(id="FIT-C002", rol=Rol.SOCIO)
RECEPCION = Actor(id="FIT-R001", rol=Rol.RECEPCION)
INSTRUCTOR = Actor(id="FIT-I001", rol=Rol.INSTRUCTOR)


# ==========================================
# BR-03: Recepción reserva/cancela a nombre del socio; un socio solo lo suyo
# ==========================================
def test_br03_recepcion_puede_reservar_y_cancelar_a_nombre_de_un_socio():
    clase = crear_clase()
    clase.reservar_lugar(SocioId("FIT-C001"), RECEPCION, ReservaId("R1"))
    clase.cancelar_reserva(SocioId("FIT-C001"), RECEPCION)
    assert clase._reservas[0].estado == EstadoDeReserva.CANCELADA


def test_br03_socio_puede_cancelar_su_propia_reserva():
    clase = crear_clase()
    clase.reservar_lugar(SocioId("FIT-C001"), SOCIO_1, ReservaId("R1"))
    clase.cancelar_reserva(SocioId("FIT-C001"), SOCIO_1)
    assert clase.lugares_disponibles() == 5


def test_br03_socio_no_puede_cancelar_la_reserva_de_otro_socio():
    clase = crear_clase()
    clase.reservar_lugar(SocioId("FIT-C001"), SOCIO_1, ReservaId("R1"))
    with pytest.raises(PermissionError, match="sus propias reservas"):
        clase.cancelar_reserva(SocioId("FIT-C001"), SOCIO_2)


def test_br03_socio_no_puede_reservar_a_nombre_de_otro_socio():
    clase = crear_clase()
    with pytest.raises(PermissionError, match="propio nombre"):
        clase.reservar_lugar(SocioId("FIT-C001"), SOCIO_2, ReservaId("R1"))


def test_br03_instructor_no_puede_cancelar_reservas():
    clase = crear_clase()
    clase.reservar_lugar(SocioId("FIT-C001"), SOCIO_1, ReservaId("R1"))
    with pytest.raises(PermissionError, match="Solo el socio o recepción"):
        clase.cancelar_reserva(SocioId("FIT-C001"), INSTRUCTOR)


# ==========================================
# BR-07: La clase debe estar incluida en el plan
# ==========================================
def test_br07_clase_incluida_en_el_plan():
    plan = PlanDeMembresia(PlanId("P"), "Plan Básico", ["Mensual", "Anual"])
    assert ClaseIncluidaEnPlanSpec("Clase Mensual 01").is_satisfied_by(plan)


def test_br07_clase_fuera_del_plan_es_rechazada():
    plan = PlanDeMembresia(PlanId("P"), "Plan Básico", ["Mensual"])
    assert not ClaseIncluidaEnPlanSpec("Clase Anual 04").is_satisfied_by(plan)


def test_br07_comparacion_ignora_mayusculas_y_espacios():
    plan = PlanDeMembresia(PlanId("P"), "Plan", ["  mensual "])
    assert ClaseIncluidaEnPlanSpec("CLASE MENSUAL 05").is_satisfied_by(plan)


def test_br07_plan_sin_clases_no_incluye_nada():
    plan = PlanDeMembresia(PlanId("P"), "Plan vacío", ["", " "])
    assert not ClaseIncluidaEnPlanSpec("Clase Mensual 01").is_satisfied_by(plan)


# ==========================================
# BR-08 / BR-09: No-show al cerrar la clase, sin sanción
# ==========================================
def test_br08_reserva_activa_sin_asistencia_se_vuelve_no_show():
    ayer = datetime.now() - timedelta(days=1)
    clase = crear_clase(inicio=ayer, fin=ayer + timedelta(hours=1))
    clase.reservar_lugar(SocioId("FIT-C001"), SOCIO_1, ReservaId("R1"))  # no llega
    clase.reservar_lugar(SocioId("FIT-C002"), SOCIO_2, ReservaId("R2"))  # sí llega
    clase.reservar_lugar(SocioId("FIT-C003"), RECEPCION, ReservaId("R3"))  # cancela
    clase.registrar_asistencia(SocioId("FIT-C002"), RECEPCION)
    clase.cancelar_reserva(SocioId("FIT-C003"), RECEPCION)

    clase.procesar_cierre_de_clase()

    estados = {r.socio_id: r.estado for r in clase._reservas}
    assert estados["FIT-C001"] == EstadoDeReserva.NO_SHOW
    assert estados["FIT-C002"] == EstadoDeReserva.ASISTIDA
    assert estados["FIT-C003"] == EstadoDeReserva.CANCELADA  # cancelada ≠ no-show


def test_br08_no_se_puede_cerrar_una_clase_que_no_ha_terminado():
    clase = crear_clase()  # termina dentro de 1 hora
    with pytest.raises(ValueError, match="antes de que la clase termine"):
        clase.procesar_cierre_de_clase()
