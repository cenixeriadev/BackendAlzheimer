# 📅 Módulo de Gestión de Citas

## Descripción
Módulo completo para gestión de citas médicas con **lógica de permisos híbrida** basada en el estado del paciente (independiente o con cuidador).

---

## 🎯 Modelo de Permisos (Opción C - Híbrido)

### **Paciente Independiente** (`estado_alzheimer = 'independiente'`)
- ✅ Puede crear sus propias citas
- ✅ Puede ver y gestionar sus citas
- ✅ Puede cancelar/reprogramar
- ❌ No puede crear citas para otros

### **Paciente con Cuidador** (`estado_alzheimer = 'con_cuidador'`)
- ❌ **NO puede crear citas** (debe hacerlo el cuidador)
- ✅ Puede VER sus citas
- ❌ No puede modificar ni cancelar (solo el cuidador)

### **Cuidador**
- ✅ Puede crear citas para sus pacientes asignados
- ✅ Puede ver todas las citas de sus pacientes
- ✅ Puede cancelar/reprogramar citas
- ✅ Puede agregar notas

### **Médico**
- ✅ Puede ver SUS citas asignadas
- ✅ Puede actualizar notas médicas
- ✅ Puede marcar citas como completadas
- ❌ No puede crear citas

### **Admin**
- ✅ Acceso total a todas las citas
- ✅ Puede crear citas para cualquier paciente
- ✅ Puede gestionar todo

---

## 📂 Estructura del Módulo

```
app/
├── models/
│   ├── cita.py              # Modelo SQLAlchemy de Cita
│   └── hospital.py          # Modelo SQLAlchemy de Hospital
├── schemas/
│   └── cita.py              # Schemas Pydantic (validaciones)
├── services/
│   └── cita_service.py      # Lógica de negocio y permisos
└── routers/
    └── cita.py              # Endpoints de la API
```

---

## 🔌 API Endpoints

### **Gestión de Citas**

#### 1. Crear Cita
```http
POST /api/citas
Authorization: Bearer <token>
Content-Type: application/json

{
  "paciente_id": 5,
  "medico_id": 3,
  "hospital_id": 1,
  "fecha_hora": "2025-11-15T10:00:00",
  "motivo": "Control mensual y revisión de resonancias",
  "notas": "Paciente reporta mayor desorientación"
}
```

**Respuesta:**
```json
{
  "id": 1,
  "paciente_id": 5,
  "medico_id": 3,
  "hospital_id": 1,
  "fecha_hora": "2025-11-15T10:00:00",
  "estado": "programada",
  "motivo": "Control mensual...",
  "notas": "Paciente reporta...",
  "paciente_nombre": "Juan",
  "paciente_apellido": "Pérez",
  "medico_nombre": "Dra. María",
  "medico_apellido": "González",
  "hospital_nombre": "Hospital Nacional",
  "created_at": "2025-11-07T...",
  "updated_at": "2025-11-07T..."
}
```

---

#### 2. Listar Citas (con filtros)
```http
GET /api/citas?estado=programada&page=1&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
- `paciente_id` (int): Filtrar por paciente
- `medico_id` (int): Filtrar por médico
- `hospital_id` (int): Filtrar por hospital
- `estado` (enum): programada | completada | cancelada | reprogramada
- `fecha_desde` (string): YYYY-MM-DD
- `fecha_hasta` (string): YYYY-MM-DD
- `page` (int): Número de página (default: 1)
- `limit` (int): Registros por página (default: 10, max: 100)

**Respuesta:**
```json
{
  "total": 45,
  "page": 1,
  "limit": 10,
  "total_pages": 5,
  "citas": [...]
}
```

---

#### 3. Obtener Detalle de Cita
```http
GET /api/citas/{cita_id}
Authorization: Bearer <token>
```

---

#### 4. Obtener Citas de un Paciente
```http
GET /api/citas/paciente/5?estado=programada
Authorization: Bearer <token>
```

---

#### 5. Obtener Citas de un Médico
```http
GET /api/citas/medico/3?fecha_desde=2025-11-01&fecha_hasta=2025-11-30
Authorization: Bearer <token>
```

---

#### 6. Obtener Mis Próximas Citas
```http
GET /api/citas/proximas/mis-citas?dias=7
Authorization: Bearer <token>
```

---

#### 7. Actualizar Cita
```http
PUT /api/citas/{cita_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "fecha_hora": "2025-11-16T14:00:00",
  "notas": "Reagendado por solicitud del paciente"
}
```

---

#### 8. Cambiar Estado de Cita
```http
PATCH /api/citas/{cita_id}/estado
Authorization: Bearer <token>
Content-Type: application/json

{
  "estado": "completada",
  "motivo_cambio": "Consulta finalizada exitosamente"
}
```

---

#### 9. Cancelar Cita
```http
DELETE /api/citas/{cita_id}?motivo=Paciente no puede asistir por emergencia familiar
Authorization: Bearer <token>
```

---

### **Consulta de Disponibilidad**

#### 10. Consultar Disponibilidad de Médico
```http
GET /api/citas/disponibilidad/medico?medico_id=3&fecha=2025-11-15
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "medico_id": 3,
  "fecha": "2025-11-15",
  "horarios": [
    {
      "hora_inicio": "08:00",
      "hora_fin": "09:00",
      "disponible": true
    },
    {
      "hora_inicio": "09:00",
      "hora_fin": "10:00",
      "disponible": false
    },
    {
      "hora_inicio": "10:00",
      "hora_fin": "11:00",
      "disponible": true
    },
    ...
  ]
}
```

---

## 🔒 Validaciones Automáticas

### **Al Crear una Cita:**
1. ✅ Valida que el paciente exista
2. ✅ Valida que el médico exista
3. ✅ Valida que el hospital exista (si se proporciona)
4. ✅ Valida permisos según tipo de usuario
5. ✅ Valida que la fecha sea futura
6. ✅ Valida que no haya conflicto de horario con el médico
7. ✅ Para pacientes con cuidador: solo el cuidador puede crear

### **Al Actualizar/Cancelar:**
1. ✅ Valida permisos de gestión
2. ✅ No permite modificar citas completadas o canceladas
3. ✅ Valida nueva disponibilidad si cambia la fecha

---

## 💡 Ejemplos de Uso por Tipo de Usuario

### **Ejemplo 1: Paciente Independiente crea su cita**
```bash
# Login como paciente (estado_alzheimer = 'independiente')
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "juan.paciente", "password": "123456"}'

# Respuesta: { "access_token": "...", "tipo_usuario": "paciente" }

# Crear cita
curl -X POST http://localhost:8000/api/citas \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 5,
    "medico_id": 3,
    "hospital_id": 1,
    "fecha_hora": "2025-11-20T10:00:00",
    "motivo": "Control mensual"
  }'

# ✅ Cita creada exitosamente
```

---

### **Ejemplo 2: Paciente con Cuidador intenta crear cita**
```bash
# Login como paciente (estado_alzheimer = 'con_cuidador')
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "pedro.paciente", "password": "123456"}'

# Crear cita
curl -X POST http://localhost:8000/api/citas \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 10,
    "medico_id": 3,
    "hospital_id": 1,
    "fecha_hora": "2025-11-20T10:00:00",
    "motivo": "Control"
  }'

# ❌ Error 403: "Las citas deben ser gestionadas por su cuidador asignado"
```

---

### **Ejemplo 3: Cuidador crea cita para su paciente**
```bash
# Login como cuidador
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "maria.cuidadora", "password": "123456"}'

# Crear cita para paciente asignado (id=10)
curl -X POST http://localhost:8000/api/citas \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 10,
    "medico_id": 3,
    "hospital_id": 1,
    "fecha_hora": "2025-11-20T10:00:00",
    "motivo": "Control mensual",
    "notas": "Paciente ha mostrado mayor confusión esta semana"
  }'

# ✅ Cita creada exitosamente

# Ver todas las citas de mis pacientes
curl -X GET http://localhost:8000/api/citas \
  -H "Authorization: Bearer <token>"

# ✅ Retorna citas de todos los pacientes a cargo
```

---

### **Ejemplo 4: Médico consulta sus citas del día**
```bash
# Login como médico
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dr.gomez", "password": "123456"}'

# Ver mis citas de hoy
curl -X GET "http://localhost:8000/api/citas?fecha_desde=2025-11-07&fecha_hasta=2025-11-07&estado=programada" \
  -H "Authorization: Bearer <token>"

# Marcar cita como completada
curl -X PATCH http://localhost:8000/api/citas/15/estado \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada",
    "motivo_cambio": "Consulta finalizada. Paciente estable."
  }'
```

---

## 🧪 Testing

### Ejecutar Tests
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/test_cita.py -v
```

---

## 🚀 Instalación y Configuración

### 1. La BD ya está lista
Tu tabla `cita` ya existe en el schema. No necesitas ejecutar migraciones adicionales.

### 2. El módulo ya está integrado
Los archivos están creados y el router ya está registrado en `main.py`.

### 3. Reinicia el servidor
```bash
# En tu terminal PowerShell
python run.py
```

### 4. Verifica en la documentación
```
http://localhost:8000/docs
```

Verás todos los endpoints de `/api/citas` documentados automáticamente.

---

## 📊 Base de Datos - Tabla Cita

La tabla ya existe en tu BD:
```sql
CREATE TABLE cita (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    medico_id INTEGER NOT NULL REFERENCES medico(id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES hospital(id) ON DELETE SET NULL,
    fecha_hora TIMESTAMP NOT NULL,
    estado VARCHAR(50) DEFAULT 'programada' 
        CHECK (estado IN ('programada', 'completada', 'cancelada', 'reprogramada')),
    motivo TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices ya creados:**
- `idx_cita_paciente_id`
- `idx_cita_medico_id`
- `idx_cita_fecha_hora`

---

## 🎨 Características Destacadas

### ✅ Gestión Inteligente de Permisos
- Lógica híbrida basada en `estado_alzheimer` del paciente
- Validación automática de roles y relaciones

### ✅ Prevención de Conflictos
- Detecta automáticamente conflictos de horario
- Valida disponibilidad del médico antes de agendar

### ✅ Auditoría Completa
- Registro automático de cambios de estado
- Tracking de quién modificó qué

### ✅ API REST Completa
- Endpoints para todas las operaciones CRUD
- Filtros avanzados y paginación
- Consulta de disponibilidad

### ✅ Documentación Automática
- OpenAPI/Swagger integrado
- Ejemplos de uso en `/docs`

---

## 📝 Próximas Mejoras (Opcionales)

- [ ] Sistema de notificaciones (email/SMS)
- [ ] Recordatorios automáticos 24h antes
- [ ] Calendario visual de disponibilidad
- [ ] Reprogramación automática en caso de cancelación
- [ ] Integración con sistema de videollamadas
- [ ] Reportes de asistencia y puntualidad

---

## 🆘 Troubleshooting

### Error: "Médico ya tiene cita en ese horario"
- **Solución**: Consulta la disponibilidad con `/api/citas/disponibilidad/medico` antes de agendar

### Error: "Las citas deben ser gestionadas por su cuidador"
- **Causa**: Paciente tiene `estado_alzheimer = 'con_cuidador'`
- **Solución**: El cuidador debe crear la cita

### Error: "No es el cuidador asignado a este paciente"
- **Causa**: El cuidador no está asignado al paciente
- **Solución**: Verifica que `paciente.cuidador_id` esté correctamente configurado

---

## 📞 Soporte

Para dudas o problemas:
- Revisa la documentación en `/docs`
- Consulta los logs del servidor
- Verifica los permisos en la base de datos

---

**¡Módulo de Citas listo para usar! 🎉**
