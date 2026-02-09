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

### Modelo de datos

```
┌──────────┐       ┌──────────┐       ┌──────────────┐
│  User    │1──── N│  Field   │1──── N│ WeatherData  │
└──────────┘       └──────────┘       └──────────────┘
     │1                  │1
     │                   │
     N                   N
┌──────────┐       ┌──────────┐
│  Alert   │       │  Alert   │
└──────────┘       └──────────┘
     │1
     │
     N
┌──────────────┐
│ Notification │
└──────────────┘
```

- **User**: Usuarios del sistema
- **Field**: Campos/parcelas asociados a un usuario con ubicación geográfica
- **WeatherData**: Datos meteorológicos por campo y fecha (probabilidades de helada, granizo, lluvia)
- **Alert**: Configuración de umbrales por usuario, campo y tipo de evento
- **Notification**: Notificaciones generadas cuando un umbral es superado

---

### Decisiones de diseño

| Decisión | Justificación |
|---|---|
| **Async completo** | SQLAlchemy async + FastAPI async para máxima concurrencia sin bloquear el event loop |
| **Repository pattern** | Desacopla la lógica de negocio del acceso a datos, facilita testing y mantenimiento |
| **Observer pattern (EventBus)** | Desacopla la evaluación de alertas de la creación de notificaciones; permite agregar nuevos handlers sin modificar el flujo principal |
| **Bulk insert de notificaciones** | Las notificaciones se acumulan en memoria y se insertan en batch para reducir queries a la DB |
| **Background job con asyncio** | Evaluación periódica sin dependencias externas (no requiere Celery/Redis) |
| **UUIDs como primary keys** | Evita IDs secuenciales predecibles, mejor para sistemas distribuidos |
| **Alembic migrations** | Versionado del schema de base de datos, reproducible en cualquier entorno |
| **Pydantic v2 schemas** | Validación robusta de entrada/salida con serialización automática |
| **Seed data** | Datos de prueba que demuestran los escenarios de alertas disparadas y no disparadas |

---

### Requisitos

- **Docker Desktop** (incluye Docker Engine y Docker Compose)
- **make** (incluido en macOS/Linux; en Windows usar WSL2 o instalar con `choco install make`)

---

### Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd agrobot

# 2. Levantar todo (build + migraciones + seed automático)
make init

# 3. Abrir la documentación interactiva
# http://localhost:8000/docs
```

La API estará disponible en `http://localhost:8000` y la documentación Swagger en `http://localhost:8000/docs`.

---

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
| `make lint` | Analiza el código con ruff |
| `make format` | Formatea el código con ruff |

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
