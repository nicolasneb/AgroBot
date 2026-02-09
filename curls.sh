
# ============================================
#  🌾 Weather Alert System - cURL Examples
# ============================================
# Base URL: http://localhost:8000

# ────────────────────────────────────────────
#  Health Check
# ────────────────────────────────────────────

curl -s http://localhost:8000/health | python -m json.tool

# ────────────────────────────────────────────
#  👤 Users
# ────────────────────────────────────────────

# Crear usuario
curl -s -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Juan Pérez", "phone": "+5491155551234"}' | python -m json.tool

# Listar usuarios (con paginación)
curl -s "http://localhost:8000/users/?skip=0&limit=10" | python -m json.tool

# Obtener usuario por ID
curl -s http://localhost:8000/users/{user_id} | python -m json.tool

# ────────────────────────────────────────────
#  🌱 Fields
# ────────────────────────────────────────────

# Crear campo
curl -s -X POST http://localhost:8000/fields/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "name": "Campo Norte",
    "latitude": -34.6037,
    "longitude": -58.3816
  }' | python -m json.tool

# Listar campos de un usuario
curl -s "http://localhost:8000/fields/user/{user_id}?skip=0&limit=10" | python -m json.tool

# Obtener campo por ID
curl -s http://localhost:8000/fields/{field_id} | python -m json.tool

# ────────────────────────────────────────────
#  🌦️ Weather Data
# ────────────────────────────────────────────

# Crear dato meteorológico
curl -s -X POST http://localhost:8000/weather/ \
  -H "Content-Type: application/json" \
  -d '{
    "field_id": "{field_id}",
    "event_type": "lluvia",
    "probability": 85.0,
    "target_date": "2026-02-15"
  }' | python -m json.tool

# Listar datos meteorológicos de un campo
curl -s "http://localhost:8000/weather/field/{field_id}?skip=0&limit=10" | python -m json.tool

# ────────────────────────────────────────────
#  🚨 Alerts
# ────────────────────────────────────────────

# Crear alerta
curl -s -X POST http://localhost:8000/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "field_id": "{field_id}",
    "event_type": "lluvia",
    "threshold": 70.0
  }' | python -m json.tool

# Listar alertas de un usuario
curl -s "http://localhost:8000/alerts/user/{user_id}?skip=0&limit=10" | python -m json.tool

# Obtener alerta por ID
curl -s http://localhost:8000/alerts/{alert_id} | python -m json.tool

# Actualizar alerta (threshold y/o is_active)
curl -s -X PATCH http://localhost:8000/alerts/{alert_id} \
  -H "Content-Type: application/json" \
  -d '{"threshold": 80.0, "is_active": false}' | python -m json.tool

# Eliminar alerta
curl -s -X DELETE http://localhost:8000/alerts/{alert_id}

# ────────────────────────────────────────────
#  🔔 Notifications
# ────────────────────────────────────────────

# Listar notificaciones de un usuario
curl -s "http://localhost:8000/notifications/user/{user_id}?skip=0&limit=10" | python -m json.tool

# Listar solo no leídas
curl -s "http://localhost:8000/notifications/user/{user_id}?unread_only=true" | python -m json.tool

# Marcar notificación como leída
curl -s -X PATCH http://localhost:8000/notifications/{notification_id}/read | python -m json.tool

# ────────────────────────────────────────────
#  🔄 Flujo completo de prueba
# ────────────────────────────────────────────

# 1. Crear usuario
# 2. Crear campo con el user_id obtenido
# 3. Crear dato meteorológico con el field_id obtenido
# 4. Crear alerta con user_id, field_id y un threshold menor a la probability
# 5. Esperar a que el background job evalúe (según EVALUATION_INTERVAL_SECONDS)
# 6. Consultar notificaciones del usuario
