"""
Pruebas de INTEGRACIÓN (API + base de datos) de las reglas corregidas:
BR-03, BR-06 (en asistencia), BR-07 y BR-08.
Usan las fixtures de conftest.py: base de datos en memoria con los CSV cargados.
"""
from datetime import datetime, timedelta

from src.infrastructure.orm import (
    PlanDeMembresiaORM,
    MembresiaORM,
    ClaseGrupalORM,
)

API = "/api/v1"


def comando(clase_id, socio_id, actor_id, actor_rol):
    """Arma el JSON que esperan los endpoints de reservas."""
    return {
        "clase_id": clase_id,
        "socio_id": socio_id,
        "actor_id": actor_id,
        "actor_rol": actor_rol,
    }


def membresia_de(db, socio_id):
    return db.query(MembresiaORM).filter(MembresiaORM.socio_id == socio_id).first()


# ==========================================
# BR-07: Clase fuera del plan
# ==========================================
def test_br07_reserva_rechazada_si_la_clase_no_esta_en_el_plan(cliente_api, db_session):
    # El socio FIT-C001 cambia a un plan que SOLO incluye clases "Mensual"
    db_session.add(
        PlanDeMembresiaORM(id="PLAN-BASICO", nombre="Plan Básico", clases_incluidas="Mensual")
    )
    membresia_de(db_session, "FIT-C001").plan_id = "PLAN-BASICO"
    db_session.commit()

    # FIT-P004 es "Clase Anual 04" → no está en su plan
    r = cliente_api.post(f"{API}/reservas", json=comando("FIT-P004", "FIT-C001", "FIT-C001", "Socio"))
    assert r.status_code == 400
    assert "no está incluida en tu plan" in r.json()["mensaje"]
    assert "actualizar tu plan" in r.json()["mensaje"]

    # FIT-P001 es "Clase Mensual 01" → sí está en su plan
    r = cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C001", "FIT-C001", "Socio"))
    assert r.status_code == 201


# ==========================================
# BR-06: Membresía suspendida no puede registrar asistencia
# ==========================================
def test_br06_no_se_registra_asistencia_con_membresia_suspendida(cliente_api, db_session):
    r = cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C002", "FIT-R001", "Recepción"))
    assert r.status_code == 201

    # Después de reservar, su membresía se suspende
    membresia_de(db_session, "FIT-C002").suspendida = True
    db_session.commit()

    r = cliente_api.post(f"{API}/reservas/asistencia", json=comando("FIT-P001", "FIT-C002", "FIT-R001", "Recepción"))
    assert r.status_code == 400
    assert "no está vigente" in r.json()["mensaje"]


def test_br06_asistencia_con_membresia_vigente_funciona(cliente_api):
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C003", "FIT-R001", "Recepción"))
    r = cliente_api.post(f"{API}/reservas/asistencia", json=comando("FIT-P001", "FIT-C003", "FIT-R001", "Recepción"))
    assert r.status_code == 200
    assert r.json()["nuevo_estado"] == "ASISTIDA"


# ==========================================
# BR-03: Quién puede cancelar
# ==========================================
def test_br03_instructor_no_puede_cancelar_reservas(cliente_api):
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C004", "FIT-C004", "Socio"))
    r = cliente_api.post(f"{API}/reservas/cancelar", json=comando("FIT-P001", "FIT-C004", "FIT-I001", "Instructor"))
    assert r.status_code == 403


def test_br03_socio_no_puede_cancelar_reserva_ajena(cliente_api):
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C005", "FIT-C005", "Socio"))
    r = cliente_api.post(f"{API}/reservas/cancelar", json=comando("FIT-P001", "FIT-C005", "FIT-C006", "Socio"))
    assert r.status_code == 403


def test_br03_recepcion_cancela_a_nombre_del_socio(cliente_api):
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P001", "FIT-C008", "FIT-C008", "Socio"))
    r = cliente_api.post(f"{API}/reservas/cancelar", json=comando("FIT-P001", "FIT-C008", "FIT-R001", "Recepción"))
    assert r.status_code == 200
    assert r.json()["nuevo_estado"] == "CANCELADA"


# ==========================================
# BR-08 / BR-09: Cierre de clase y no-shows
# ==========================================
def _mover_clase(db, clase_id, inicio, fin):
    clase = db.query(ClaseGrupalORM).filter(ClaseGrupalORM.id == clase_id).first()
    clase.inicio, clase.fin = inicio, fin
    db.commit()


def test_br08_cierre_registra_no_shows(cliente_api, db_session):
    # Dos socios reservan; solo uno llega
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P002", "FIT-C010", "FIT-C010", "Socio"))
    cliente_api.post(f"{API}/reservas", json=comando("FIT-P002", "FIT-C011", "FIT-C011", "Socio"))
    cliente_api.post(f"{API}/reservas/asistencia", json=comando("FIT-P002", "FIT-C011", "FIT-R001", "Recepción"))

    # La clase ya terminó (ayer)
    ayer = datetime.now() - timedelta(days=1)
    _mover_clase(db_session, "FIT-P002", ayer, ayer + timedelta(hours=1))

    r = cliente_api.post(f"{API}/clases/FIT-P002/cierre", json={"actor_id": "FIT-A001", "actor_rol": "Administrador"})
    assert r.status_code == 200
    assert r.json()["no_shows_registrados"] == 1

    reservas = cliente_api.get(f"{API}/socios/FIT-C010/reservas").json()
    assert any(x["clase_id"] == "FIT-P002" and x["estado"] == "NO_SHOW" for x in reservas)

    # BR-09: el no-show no tiene sanción → el socio puede volver a reservar
    r = cliente_api.post(f"{API}/reservas", json=comando("FIT-P003", "FIT-C010", "FIT-C010", "Socio"))
    assert r.status_code == 201


def test_br08_recepcion_no_puede_cerrar_clases(cliente_api):
    r = cliente_api.post(f"{API}/clases/FIT-P001/cierre", json={"actor_id": "FIT-R001", "actor_rol": "Recepción"})
    assert r.status_code == 403


def test_br08_no_se_cierra_una_clase_que_no_ha_terminado(cliente_api, db_session):
    manana = datetime.now() + timedelta(days=1)
    _mover_clase(db_session, "FIT-P001", manana, manana + timedelta(hours=1))
    r = cliente_api.post(f"{API}/clases/FIT-P001/cierre", json={"actor_id": "FIT-A001", "actor_rol": "Administrador"})
    assert r.status_code == 400
