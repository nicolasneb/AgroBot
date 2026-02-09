# 🌾 AgroBot — Sistema de Alertas Climáticas

Sistema de alertas climáticas para el sector agrícola. Permite a los usuarios configurar umbrales de alerta sobre eventos meteorológicos (heladas, granizo, lluvias intensas) y recibir notificaciones automáticas cuando las condiciones climáticas superan dichos umbrales.

Desarrollado con **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL**, **Alembic** y **Docker**.

---

### Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Modelo de datos](#modelo-de-datos)
- [Decisiones de diseño](#decisiones-de-diseño)
- [Requisitos](#requisitos)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Comandos disponibles](#comandos-disponibles)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [Estructura del proyecto](#estructura-del-proyecto)

---

### Arquitectura

El proyecto sigue una **arquitectura en capas** combinada con los patrones **Repository**, **Service Layer** y **Observer**:

```
Request → Router → Service → Repository → Database
                      ↓
                   EventBus → Handlers → Notifications
```

| Capa | Responsabilidad |
|---|---|
| **Routers** | Reciben requests HTTP, validan input con Pydantic y delegan a los services |
| **Services** | Contienen la lógica de negocio y orquestan repositorios y eventos |
| **Repositories** | Abstraen el acceso a la base de datos (CRUD) |
| **EventBus** | Desacopla la generación de alertas de la creación de notificaciones (Observer pattern) |
| **Handlers** | Reaccionan a eventos emitidos por el EventBus |
| **Background Job** | Evalúa periódicamente las alertas activas contra los datos climáticos |

---

### Modelo de Datos

El esquema se diseñó con cinco entidades, cada una con una responsabilidad clara:

- **Users:** Representa a los usuarios del sistema. Se optó por incluir `phone` como identificador único ya que el contexto de Agrobot es una interfaz de WhatsApp, donde el teléfono es el canal principal de comunicación.

- **Fields:** Modela los campos de cada usuario. Se separó como entidad propia (en lugar de embeber la ubicación en el usuario) porque un mismo usuario puede tener múltiples campos en distintas ubicaciones geográficas, cada uno con condiciones climáticas diferentes.

- **WeatherData:** Almacena los datos meteorológicos que el job de ingesta persiste. Se diseñó con `event_type` y `probability` como campos separados (en lugar de columnas fijas como `frost_probability`, `rain_probability`) para permitir agregar nuevos tipos de eventos climáticos sin modificar el esquema de la base de datos. El campo `target_date` indica el día al que refiere la predicción.

- **Alerts:** Representa las alertas configuradas por los usuarios. Tiene FK tanto a `Users` como a `Fields` porque una alerta pertenece a un usuario y aplica sobre un campo específico. No tiene FK directa a `WeatherData` ya que la relación es dinámica: el background job vincula alertas con datos meteorológicos en tiempo de ejecución a través de `field_id` y `event_type`, evaluando si la `probability` supera el `threshold` configurado.

- **Notifications:** Registra las notificaciones generadas cuando una alerta se dispara. Tiene FK a `Users` (para consultar notificaciones por usuario) y a `Alerts` (para trazabilidad de qué alerta la originó). El campo `is_read` permite gestionar el estado de lectura desde el frontend.

```
┌──────────────────────────┐
│          USERS           │
├──────────────────────────┤
│ id: UUID (PK)            │
│ name: String(100)        │
│ phone: String(20) UNIQUE │
│ created_at: DateTime     │
└──────────┬───────────────┘
           │
     ┌─────┼──────────────────────┐
     │1    │1                     │1
     │N    │N                     │N
┌────▼─────────────────┐  ┌──────▼───────────────────┐  ┌──────────────────────────┐
│        FIELDS        │  │         ALERTS           │  │     NOTIFICATIONS        │
├──────────────────────┤  ├──────────────────────────┤  ├──────────────────────────┤
│ id: UUID (PK)        │  │ id: UUID (PK)            │  │ id: UUID (PK)            │
│ user_id: UUID (FK)   │  │ user_id: UUID (FK)       │  │ user_id: UUID (FK)       │
│ name: String(100)    │  │ field_id: UUID (FK)      │  │ alert_id: UUID (FK)      │
│ latitude: Float      │  │ event_type: String(50)   │  │ message: String          │
│ longitude: Float     │  │ threshold: Float         │  │ is_read: Boolean         │
│ created_at: DateTime │  │ is_active: Boolean       │  │ created_at: DateTime     │
└──────┬───────────────┘  │ created_at: DateTime     │  └──────────────────────────┘
       │                  └──────────┬───────────────┘             ▲
       │                             │                             │
       │1                            │1                            │N
       │N                            └─────────────────────────────┘
┌──────▼───────────────────┐              (Alerts 1──N Notifications)
│      WEATHER_DATA        │
├──────────────────────────┤
│ id: UUID (PK)            │
│ field_id: UUID (FK)      │
│ event_type: String(50)   │
│ probability: Float       │
│ target_date: Date        │
│ created_at: DateTime     │
└──────────────────────────┘
```
```
Relaciones:
  Users     1──N  Fields          (fields.user_id → users.id)
  Users     1──N  Alerts          (alerts.user_id → users.id)
  Users     1──N  Notifications   (notifications.user_id → users.id)
  Fields    1──N  WeatherData     (weather_data.field_id → fields.id)
  Fields    1──N  Alerts          (alerts.field_id → fields.id)
  Alerts    1──N  Notifications   (notifications.alert_id → alerts.id)

Nota: No existe FK directa entre WeatherData y Alerts.
Se vinculan por lógica de negocio (field_id + event_type).
```

- **User**: Usuarios del sistema
- **Field**: Campos/parcelas asociados a un usuario con ubicación geográfica
- **WeatherData**: Datos meteorológicos por campo y fecha (probabilidades de helada, granizo, lluvia)
- **Alert**: Configuración de umbrales por usuario, campo y tipo de evento
- **Notification**: Notificaciones generadas cuando un umbral es superado

---

## Decisiones de Diseño

El desarrollo del sistema comenzó con la definición de una **arquitectura por capas** (Routers → Services → Repositories → Models), complementada con los patrones **Repository** y **Service Layer**, buscando una separación clara de responsabilidades que facilite el testing y la mantenibilidad del código.

Se incorporó el patrón **Observer** mediante un Event Bus para desacoplar la lógica de evaluación de alertas de la generación de notificaciones, permitiendo agregar nuevos handlers (logs, emails, webhooks) sin modificar el flujo principal.

El **modelo de datos** se diseñó con cinco entidades (Users, Fields, WeatherData, Alerts, Notifications) donde WeatherData y Alerts no tienen FK directa entre sí, sino que se vinculan por lógica de negocio a través de `field_id` y `event_type`, reflejando que la relación es evaluada dinámicamente por el background job y no es una dependencia estructural.

Se eligió **asincronía** de punta a punta (`AsyncSession`, `async/await` en repositorios, servicios y routers) para maximizar la concurrencia y evitar bloqueos del event loop, algo crítico en un sistema que combina endpoints HTTP con un job periódico corriendo en el mismo proceso.

El **background job** se implementó como una tarea asyncio dentro del lifespan de FastAPI, evaluando periódicamente los umbrales configurados contra los datos meteorológicos y emitiendo eventos cuando se superan, sin necesidad de dependencias externas como Celery.

### Escalabilidad

Pensando en el crecimiento del sistema, se tomaron las siguientes decisiones:

- **Índices compuestos:** Se agregaron índices como `ix_weather_field_event_date` sobre `field_id`, `event_type` y `target_date` para optimizar las consultas más frecuentes y evitar full table scans a medida que crece el volumen de datos meteorológicos.
- **Paginación:** Se implementó en los endpoints de listado para controlar el tamaño de las respuestas y evitar la transferencia de grandes volúmenes de datos en una sola request.
- **Connection Pooling:** Se configuró en SQLAlchemy para reutilizar conexiones a la base de datos y evitar el overhead de abrir y cerrar conexiones en cada operación, fundamental bajo alta concurrencia.
- **Evaluación por lotes (batches):** El background job procesa las alertas en grupos controlados en lugar de cargar todas en memoria simultáneamente, evitando picos de consumo de recursos cuando la cantidad de alertas activas escala.

### Developer Experience

Se priorizó la experiencia del evaluador con:

- `Makefile` que centraliza todos los comandos del proyecto.
- `docker-compose` para levantar el entorno completo con un solo comando.
- Migraciones Alembic funcionales.
- Seed data con escenarios que disparan alertas reales.
- Tests que cubren desde repositorios hasta el flujo completo de evaluación.

---

### Requisitos

- **Docker Desktop** (incluye Docker Engine y Docker Compose)
- **make** (incluido en macOS/Linux; en Windows usar WSL2 o instalar con `choco install make`)

---

### Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/nicolasneb/AgroBot
cd agrobot

# 2. Levantar todo (build + migraciones + seed automático)
make init

# 3. Abrir la documentación interactiva
# http://localhost:8000/docs

# 4. Ver logs donde podremos observar las notificaciones (por default se ejecuta el job cada 60s)
make logs
```

La API estará disponible en `http://localhost:8000` y la documentación Swagger en `http://localhost:8000/docs`.

---

> **Nota:** Si el build falla con un error de snapshot (`parent snapshot does not exist`),
> ejecutar `docker builder prune -f` y reintentar con `make init`.
> Esta aclaracion esta hecha debido a que me encontre con dicho problema una vez a lo largo del desarrollo

### Comandos disponibles

| Comando | Descripción |
|---|---|
| `make init` | Setup inicial: build, migraciones y levanta los servicios |
| `make build` | Rebuild y levanta los containers |
| `make up` | Levanta los containers (sin rebuild) |
| `make down` | Detiene los containers |
| `make restart` | Rebuild completo |
| `make reset` | Borra volúmenes y reinicia desde cero |
| `make logs` | Muestra logs de la API en tiempo real |
| `make shell` | Abre una terminal dentro del container de la API |
| `make db-shell` | Abre `psql` conectado a la base de datos |
| `make migrate` | Ejecuta las migraciones pendientes |
| `make migrate-create name="descripcion"` | Crea una nueva migración |
| `make migrate-history` | Muestra el historial de migraciones |
| `make migrate-downgrade` | Revierte la última migración |
| `make seed` | Carga datos de prueba |
| `make test` | Ejecuta los tests |
| `make test-cov` | Ejecuta los tests con reporte de cobertura |

---

### API Endpoints

#### Users
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/users/` | Crear usuario |
| `GET` | `/users/` | Listar usuarios |
| `GET` | `/users/{id}` | Obtener usuario por ID |

#### Fields
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/fields/` | Crear campo |
| `GET` | `/fields/` | Listar campos |
| `GET` | `/fields/{id}` | Obtener campo por ID |
| `GET` | `/fields/user/{user_id}` | Campos de un usuario |

#### Weather Data
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/weather/` | Registrar datos climáticos |
| `GET` | `/weather/field/{field_id}` | Datos climáticos de un campo |

#### Alerts
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/alerts/` | Crear alerta |
| `GET` | `/alerts/user/{user_id}` | Alertas de un usuario |
| `GET` | `/alerts/{id}` | Obtener alerta por ID |
| `PUT` | `/alerts/{id}` | Actualizar alerta |
| `DELETE` | `/alerts/{id}` | Eliminar alerta |

#### Notifications
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/notifications/user/{user_id}` | Notificaciones de un usuario |
| `PATCH` | `/notifications/{id}/read` | Marcar como leída |

#### Health
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de la API y conectividad a la DB |

---

### Tests

```bash
# Ejecutar todos los tests
make test

# Tests con reporte de cobertura
make test-cov
```


Los tests cubren:

- **Repositories**: CRUD de cada entidad contra la base de datos de test
- **Services**: Lógica de negocio de alertas y evaluación
- **Routers**: Tests de integración de todos los endpoints (happy path + errores)
- **EventBus**: Emisión de eventos y ejecución de handlers
- **Handlers**: Acumulación y flush de notificaciones
- **Background Job**: Ejecución periódica del servicio de evaluación
- **Seed**: Idempotencia de la carga de datos

---

### Variables de Entorno

El archivo `.env` en la raíz del proyecto configura todo el sistema. A continuación el detalle de cada variable:

> **Nota:** Deje subido el .env para este challenge ya que facilita levantar el entorno rápidamente soy consciente de que no es una buena practica dejarlo, esta comentada la linea referida el .env en el .gitignore

#### PostgreSQL

| Variable | Descripción | Default |
|---|---|---|
| `POSTGRES_USER` | Usuario de la base de datos | `postgres` |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos | `postgres` |
| `POSTGRES_DB` | Nombre de la base de datos | `agrobot` |
| `POSTGRES_PORT` | Puerto de PostgreSQL | `5432` |

#### Application

| Variable | Descripción | Default |
|---|---|---|
| `DATABASE_URL` | Connection string async para SQLAlchemy (`asyncpg`) | Compuesta desde las variables de PostgreSQL |
| `TEST_DATABASE_URL` | Connection string async para la base de datos de tests | `""` (vacío) |
| `ALEMBIC_DATABASE_URL` | Connection string sync para Alembic (`psycopg2`) | `""` (vacío) |

#### Background Job

| Variable | Descripción | Default |
|---|---|---|
| `EVALUATION_INTERVAL_SECONDS` | Intervalo en segundos entre cada ejecución del job de evaluación de alertas | `60` |

> **Nota:** Las variables `DATABASE_URL`, `TEST_DATABASE_URL` y `ALEMBIC_DATABASE_URL` se componen dinámicamente usando interpolación de variables en el `.env`. No es necesario modificarlas directamente, basta con ajustar las variables de PostgreSQL.
>
> Se usan dos drivers distintos porque SQLAlchemy async requiere `asyncpg` mientras que Alembic opera de forma sincrónica con `psycopg2`.

---

### cURL Examples

El archivo `curls.sh` contiene todos los comandos para probar la API.

---

### Estructura del proyecto

```
.
├── app/
│   ├── main.py                  # Entry point, lifespan, routers
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # AsyncSession factory
│   ├── errors.py                # Excepciones custom y error handlers
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── field.py
│   │   ├── weather_data.py
│   │   ├── alert.py
│   │   └── notification.py
│   ├── schemas/                 # Pydantic schemas
│   │   ├── user.py
│   │   ├── field.py
│   │   ├── weather_data.py
│   │   ├── alert.py
│   │   └── notification.py
│   ├── repositories/            # Data access layer
│   │   ├── user_repo.py
│   │   ├── field_repo.py
│   │   ├── weather_repo.py
│   │   ├── alert_repo.py
│   │   └── notification_repo.py
│   ├── services/                # Business logic
│   │   ├── alert_service.py
│   │   └── evaluation_service.py
│   ├── routers/                 # HTTP endpoints
│   │   ├── users.py
│   │   ├── fields.py
│   │   ├── weather.py
│   │   ├── alerts.py
│   │   └── notifications.py
│   ├── events/                  # Observer pattern
│   │   ├── event_bus.py
│   │   ├── events.py
│   │   └── handlers/
│   │       ├── notification_handler.py
│   │       └── log_handler.py
│   ├── jobs/                    # Background tasks
│   │   └── evaluate_alerts.py
│   ├── seeds/                   # Seed data
│   │   └── seed_data.py
│   └── tests/                   # Test suite
│       ├── conftest.py
│       ├── test_user_repo.py
│       ├── test_field_repo.py
│       ├── test_alert_repo.py
│       ├── test_notification_repo.py
│       ├── test_alert_service.py
│       ├── test_evaluation_service.py
│       ├── test_event_bus.py
│       ├── test_handlers.py
│       ├── test_routers.py
│       ├── test_job.py
│       └── test_seed.py
├── alembic/                     # Database migrations
│   ├── env.py
│   └── versions/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
└── README.md
```
