# FitZone — Sistema de Gestión de Reservaciones, Membresías y Control de Accesos 🏋️‍♂️

**FitZone** es una solución de software empresarial desarrollada para la gestión automatizada de instalaciones deportivas, sesiones grupales, validación de membresías en tiempo real, colas virtuales (listas de espera) y control de asistencia/no-shows.

El proyecto resuelve la problemática de accesos inconsistentes, ausencias no notificadas (_no-shows_) y gestión manual de cupos, aplicando **Domain-Driven Design (DDD) modular**, el patrón **Specification (AND, OR, NOT)**, una **Máquina de Estados determinista** para el ciclo de vida de operaciones, y **Domain Events** con **CQRS básico**.

---

## Tabla de Contenidos

1. [Contexto del Negocio y Reglas Clave](#-contexto-del-negocio-y-reglas-clave)
2. [Trazabilidad y Artefactos de Análisis](#-trazabilidad-y-artefactos-de-análisis)
3. [Arquitectura y Patrones Aplicados](#-arquitectura-y-patrones-aplicados)
4. [Estructura del Repositorio](#-estructura-del-repositorio)
5. [Stack Tecnológico](#-stack-tecnológico)
6. [Instalación y Configuración Local](#-instalación-y-configuración-local)
7. [Pruebas Automatizadas y Cobertura (QA)](#-pruebas-automatizadas-y-cobertura-qa)
8. [Ingesta e Integración de Archivos CSV](#-ingesta-e-integración-de-archivos-csv)
9. [Despliegue y Producción (Render)](#-despliegue-y-producción-render)
10. [Swagger UI & Documentación Interactiva](#-swagger-ui--documentación-interactiva)

---

## 💼 Contexto del Negocio y Reglas Clave

El gimnasio operaba con registros manuales que generaban lugares vacíos por ausencias sin cancelar, ingresos indebidos de usuarios con membresías suspendidas y sobrecupos en sesiones populares. El sistema automatiza las siguientes reglas de negocio (Business Rules):

- **BR-01 & BR-02 (Permisos Administrativos):** Solo el Administrador puede cancelar, reprogramar o reasignar clases. El Instructor únicamente notifica su indisponibilidad.
- **BR-03 & BR-04 (Operaciones en Recepción):** El personal de Recepción puede realizar o cancelar reservaciones a nombre de un socio, pero **NUNCA** modificar membresías o contratos.
- **BR-05 (Control Estricto de Aforo):** La capacidad máxima de cada clase la establece el Administrador. No se permite sobrecupo. Al llenarse, se habilita automáticamente una lista de espera ordenada por llegada.
- **BR-06 (Vigencia de Membresía):** Membresías vencidas o suspendidas bloquean la reservación y el acceso a las instalaciones.
- **BR-07 (Inclusión en Plan):** El socio solo puede apartar clases que estén explícitamente contempladas en su plan contratado.
- **BR-08 & BR-09 (Política de No-Shows):** Una reserva activa no cancelada cuyo socio no asista al finalizar la clase se registra en el historial como _No-Show_ (sin sanción económica por el momento).
- **BR-10 (Liberación Automática):** Si un socio cancela su reserva a tiempo, el sistema notifica y ofrece el lugar inmediatamente al primer socio en la lista de espera.

---

## 📄 Trazabilidad y Artefactos de Análisis

El diseño e implementación del software derivan estrictamente de los requerimientos analizados en las Unidades 2 y 3 del curso:

- **Docs / BRD:** Ubicado en `docs/BRD.md` (Documento de Requerimientos de Negocio, User Stories con Gherkin, BPMN y Glosario Ubicuo).
- **Docs / Arquitectura:** Ubicado en `docs/architecture/ADRs.md` y `docs/architecture/diagramas.md` (Justificación de decisiones arquitectuales, diagramas UML y modelo de clases).
- **Docs / API:** Contrato OpenAPI formal en `docs/api/openapi.json`.

---

## 🏗️ Arquitectura y Patrones Aplicados

El proyecto implementa una **Arquitectura Limpia (Clean / Layered Architecture)** dividida en 4 capas estrictamente aisladas:

```text
 ┌──────────────────────────────────────────────────────────┐
 │                     API REST (FastAPI)                   │  <-- Controladores & Endpoints
 └────────────────────────────┬─────────────────────────────┘
                              │
 ┌────────────────────────────▼─────────────────────────────┐
 │                Application Layer (CQRS)                  │  <-- Commands, Queries, DTOs & Services
 └────────────────────────────┬─────────────────────────────┘
                              │
 ┌────────────────────────────▼─────────────────────────────┐
 │                     Domain Layer                         │  <-- Entidades, Specifications,
 └────────────────────────────▲─────────────────────────────┘      State Machine & Events
                              │
 ┌────────────────────────────┴─────────────────────────────┐
 │               Infrastructure Layer (ORM)                 │  <-- Repositorios, SQLAlchemy & CSV Loader
 └──────────────────────────────────────────────────────────┘
```

### Patrones de Diseño Principales

1. **Domain Model:** Las reglas residen en el agregado `ClaseGrupal`, encapsulando la consistencia de aforos y estados.
2. **Specification Pattern (AND, OR, NOT):** Permite evaluar dinámicamente si un socio cumple con las condiciones requeridas (ej. `MembresiaVigenteSpec & ClaseIncluidaEnPlanSpec`).
3. **State Machine:** Garantiza transiciones válidas de estado en las operaciones: `SOLICITADA -> ACTIVA -> SUSPENDIDA -> VENCIDA` / `CANCELADA`.
4. **Domain Events:** Emisión de eventos desacoplados (`ReservaRealizada`, `NoShowRegistrado`, `LugarOfrecidoASocio`) para actualización de historial y notificaciones.
5. **Unit of Work & Repository Pattern:** Aislamiento transaccional completo en la capa de infraestructura.

---

## 📁 Estructura del Repositorio

```text
mi-proyecto-cln/
├── .github/
│   └── workflows/
│       └── ci.yml                # Robot de Integración Continua (GitHub Actions)
├── 01_Alumno/
│   └── datos/                    # Dataset de pruebas del profesor (CSV)
│       ├── actores.csv
│       ├── catalogo.csv
│       ├── operaciones.csv
│       ├── detalle_operaciones.csv
│       ├── casos_prueba.csv
│       └── transiciones_prueba.csv
├── docs/                         # Documentación de Análisis y Arquitectura
│   ├── BRD.md
│   ├── architecture/
│   │   ├── ADRs.md
│   │   └── diagramas.md
│   └── api/
│       └── openapi.json
├── src/                          # Código fuente de la aplicación
│   ├── domain/                   # Dominio puro (Entidades, Value Objects, Specs, State Machine)
│   ├── application/              # Casos de Uso (Application Services, DTOs, CQRS, UoW)
│   ├── infrastructure/           # Persistencia (SQLAlchemy ORM, Repositorios, CSV Loader)
│   └── api/                      # Capa Web (FastAPI Routes, Middlewares, Handlers)
├── tests/                        # Suite de Pruebas Unitarias e Integración con Pytest
│   ├── conftest.py
│   ├── test_dominio.py
│   └── test_csv_integracion.py
├── .env.example                  # Plantilla de variables de entorno (12-Factor App)
├── docker-compose.yml            # Orquestador multi-contenedor (App + DB + Tests)
├── Dockerfile                    # Receta de construcción ligera (Python 3.11-slim)
├── requirements.txt              # Dependencias declaradas de Python
└── README.md                     # Documentación principal del sistema
```

---

## 🧪 Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **API Framework:** FastAPI 0.115+ / Uvicorn
- **Validación de Datos:** Pydantic v2 (con `ConfigDict` para OpenAPI)
- **Persistencia & ORM:** SQLAlchemy 2.0 (SQLite local / PostgreSQL en Docker y Producción)
- **QA & Testing:** Pytest, Pytest-Cov, HTTPX
- **Contenerización:** Docker & Docker Compose
- **CI/CD:** GitHub Actions

---

## ⚙️ Instalación y Configuración Local

### Pre-requisitos

- Python 3.11 o superior instalado.
- Git.

### Pasos de Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/tu-usuario/mi-proyecto-cln.git
   cd mi-proyecto-cln
   ```

2. **Crear y activar un entorno virtual:**
   - _En Windows (Git Bash / PowerShell):_
     ```bash
     python -m venv venv
     source venv/Scripts/activate
     ```
   - _En Linux / macOS:_
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copia el archivo `.env.example` a `.env`:

   ```bash
   cp .env.example .env
   ```

5. **Iniciar el servidor de desarrollo:**
   ```bash
   uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   La aplicación estará corriendo en `http://127.0.0.1:8000`.

---

## 🧪 Pruebas Automatizadas y Cobertura (QA)

El proyecto incluye pruebas unitarias que verifican las reglas del dominio y pruebas de integración que consumen las fixtures de los archivos CSV.

Para ejecutar la suite de pruebas completa y verificar que la cobertura cumpla con el estándar mínimo exigido (>= 80%), ejecuta:

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Reporte de Cobertura Actual (82% Verified):

```text
Name                                Stmts   Miss  Cover   Missing
------------------------------------------------------------------
src/__init__.py                         0      0   100%
src/api/main.py                        11      2    82%   21, 37
src/api/routes.py                      20      2    90%   23, 41
src/application/dtos.py                31      0   100%
src/application/services.py            51     13    75%   34, 36, 68...
src/application/unit_of_work.py        19      1    95%   21
src/domain/entities.py                107     41    62%   43, 46, 49...
src/domain/events.py                   29      0   100%
src/domain/specifications.py           42     15    64%   10, 13, 16...
src/domain/value_objects.py            83      6    93%   77, 89, 112...
src/infrastructure/csv_loader.py       40      5    88%   81, 101-104
src/infrastructure/database.py         12      4    67%   29-33
src/infrastructure/orm.py              50      0   100%
src/infrastructure/repositories.py     20      3    85%   27-28, 32
------------------------------------------------------------------
TOTAL                                 515     92    82%
```

---

## 📊 Ingesta e Integración de Archivos CSV

El módulo `src/infrastructure/csv_loader.py` actúa como un adaptador de arquitectura hexagonal. Toma los datos crudos del paquete de evaluación docente (diseñado originalmente con esquema de compras/tienda) y los traduce al modelo del gimnasio de la siguiente forma:

- **`actores.csv` (40 registros):** Carga los 40 Socios del gimnasio generando sus membresías iniciales.
- **`catalogo.csv` (20 registros):** Registra las 20 Clases Grupales asociando la columna `capacidad_o_stock` con la `Capacidad` de aforo (BR-05).
- **`operaciones.csv` (60 registros):** Se importan como las 60 solicitudes de reservación iniciales.
- **`casos_prueba.csv` (120 registros):** Evaluados al 100% en `tests/test_csv_integracion.py` contrastando las respuestas empáticas de la API (HTTP 201 Éxito / HTTP 400 Regla de Negocio).
- **`transiciones_prueba.csv` (20 registros):** Evaluados en la suite de pruebas para verificar el comportamiento de la Máquina de Estados ante solicitudes de cambio de estado.

_Nota de Dominio:_ De acuerdo con el BRD, las reglas relativas a montos de compra y carritos de productos fueron omitidas explícitamente por estar "Fuera del Alcance" (pagos y contabilidad).

---

## 🌐 Despliegue y Producción (Render)

La aplicación web y la API REST se encuentran desplegadas y en línea en el entorno de producción de Render:

- **URL de la API (Producción):** https://cln-pia-equipo11-fitzone.onrender.com
- **Swagger UI (Documentación Interactiva):** https://cln-pia-equipo11-fitzone.onrender.com/docs

---

## 📖 Swagger UI & Documentación Interactiva

FastAPI genera automáticamente la documentación interactiva en cumplimiento con OpenAPI.

Para probar la API de forma interactiva e intuitiva:

1. Inicia el servidor localmente o visita la URL de producción.
2. Entra en tu navegador a: **https://cln-pia-equipo11-fitzone.onrender.com/docs**
3. Podrás probar endpoints como:
   - `GET /api/v1/calendario`: Consulta las clases y aforos disponibles en tiempo real.
   - `POST /api/v1/reservas`: Realiza reservaciones utilizando formularios pre-llenados con validación de roles (`Socio`, `Recepción`, etc.).

---

_Desarrollado como Producto Integrador de Aprendizaje (PIA) para la materia Componentes de Lógica de Negocio — FIME, UANL._
