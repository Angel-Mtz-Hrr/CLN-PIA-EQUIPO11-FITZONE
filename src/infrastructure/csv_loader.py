import csv
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal
from .orm import (
    PlanDeMembresiaORM,
    MembresiaORM,
    ClaseGrupalORM,
    ReservaORM,
    EstadoDeReserva,
)

# Rutas a los archivos de prueba
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATOS_DIR = os.path.join(BASE_DIR, "01_Alumno", "datos")


def cargar_datos_iniciales(db: Session):
    """
    Lee los CSV del profesor y los traduce al modelo de FitZone.
    Ignora conceptos de "tienda" (precios, cantidades) y extrae solo lo útil.
    """
    print("Iniciando la traducción y carga de datos del gimnasio...")

    # 1. Crear un Plan Básico por defecto para poder validar reglas (BR-07)
    plan_basico = PlanDeMembresiaORM(
        id="PLAN-001",
        nombre="Plan Todo Incluido",
        clases_incluidas="Mensual,Trimestral,Semestral,Anual",  # Ajustado a los nombres del CSV
    )
    db.merge(plan_basico)

    # 2. Cargar ACTORES (Los convertiremos en SOCIOS con membresía activa)
    print("Cargando socios desde actores.csv...")
    with open(
        os.path.join(DATOS_DIR, "actores.csv"), mode="r", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Damos de alta al socio con una membresía ficticia válida por un año
            membresia = MembresiaORM(
                id=f"MEM-{row['actor_id']}",
                socio_id=row["actor_id"],
                plan_id="PLAN-001",
                inicio_vigencia=datetime.now() - timedelta(days=30),
                fin_vigencia=datetime.now() + timedelta(days=330),
                suspendida=False if row["activo"] == "1" else True,
            )
            db.merge(membresia)

    # 3. Cargar CATÁLOGO (Lo convertiremos en las CLASES programadas)
    print("Cargando clases desde catalogo.csv...")
    with open(
        os.path.join(DATOS_DIR, "catalogo.csv"), mode="r", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        for row in reader:
            clase = ClaseGrupalORM(
                id=row["recurso_id"],
                nombre=f"Clase {row['descripcion']}",
                # Asignamos horarios ficticios para las pruebas (hoy de 10:00 a 11:00)
                inicio=datetime.now().replace(
                    hour=10, minute=0, second=0, microsecond=0
                ),
                fin=datetime.now().replace(hour=11, minute=0, second=0, microsecond=0),
                capacidad_maxima=int(row["capacidad_o_stock"]),
            )
            db.merge(clase)

    # 4. Cargar OPERACIONES (Las convertiremos en RESERVAS iniciales)
    print("Cargando reservas desde operaciones.csv...")
    with open(
        os.path.join(DATOS_DIR, "operaciones.csv"), mode="r", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        for row in reader:
            estado = EstadoDeReserva.SOLICITADA
            if row["estado_inicial"] == "ACTIVA":
                estado = EstadoDeReserva.ACTIVA

            # Tomaremos solo la operación base como una reserva genérica
            # (El CSV detalle_operaciones.csv trae 'cantidades' y múltiples recursos,
            # lo cual rompe la regla de que 1 socio reserva 1 lugar en 1 clase.
            # Por empatía con el negocio, lo simplificamos aquí).
            reserva = ReservaORM(
                id=row["operacion_id"],
                clase_id="FIT-P001",  # Asignamos a una clase genérica para la prueba base
                socio_id=row["actor_id"],
                estado=estado,
            )
            db.merge(reserva)

    db.commit()
    print("¡Datos cargados con éxito en la base de datos de FitZone!")


if __name__ == "__main__":
    # Si ejecutamos este script directamente, creará las tablas y llenará los datos
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    cargar_datos_iniciales(db)
    db.close()
