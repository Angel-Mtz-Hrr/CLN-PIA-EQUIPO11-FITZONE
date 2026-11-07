import pytest
from datetime import datetime, timedelta
from src.domain.entities import ClaseGrupal, Membresia, PlanDeMembresia
from src.domain.value_objects import (
    ClaseId,
    SocioId,
    ReservaId,
    Capacidad,
    Horario,
    Actor,
    Rol,
    PlanId,
    MembresiaId,
    VigenciaDeMembresia,
)
from src.domain.specifications import MembresiaVigenteSpec


def test_no_se_puede_reservar_si_la_clase_esta_llena():
    # PREPARACIÓN: Una clase de prueba con cupo estricto de 1 sola persona
    horario = Horario(inicio=datetime.now(), fin=datetime.now() + timedelta(hours=1))
    clase_yoga = ClaseGrupal(
        id=ClaseId("YOGA-01"),
        nombre="Yoga Matutino",
        horario=horario,
        capacidad=Capacidad(1),
    )
    socio_1 = Actor(id="SOCIO-001", rol=Rol.SOCIO)
    socio_2 = Actor(id="SOCIO-002", rol=Rol.SOCIO)

    # ACCIÓN: El primer socio reserva (esto debe funcionar)
    clase_yoga.reservar_lugar(SocioId("SOCIO-001"), socio_1, ReservaId("RES-01"))

    # VERIFICACIÓN: El segundo socio intenta reservar y el sistema empáticamente lo detiene
    with pytest.raises(ValueError) as error:
        clase_yoga.reservar_lugar(SocioId("SOCIO-002"), socio_2, ReservaId("RES-02"))

    assert "está llena" in str(error.value)


def test_membresia_vencida_es_rechazada_amablemente():
    # PREPARACIÓN: Una membresía que venció ayer
    ayer = datetime.now() - timedelta(days=1)
    hace_un_mes = datetime.now() - timedelta(days=30)
    vigencia_caducada = VigenciaDeMembresia(inicio=hace_un_mes, vencimiento=ayer)

    membresia = Membresia(
        id=MembresiaId("MEM-01"),
        socio_id=SocioId("SOCIO-001"),
        plan_id=PlanId("PLAN-01"),
        vigencia=vigencia_caducada,
    )

    # ACCIÓN Y VERIFICACIÓN: Preguntamos a la regla si hoy es válida
    regla_vigencia = MembresiaVigenteSpec(fecha_actual=datetime.now())

    assert regla_vigencia.is_satisfied_by(membresia) is False
