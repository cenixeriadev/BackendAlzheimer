# BORRAR ANTES DE PRODUCCION

# DATOS BD

HOSTNAME = dpg-d3ofmnfdiees73b8ko70-a
PORT = 5432
DATABASE = alzhver1
USERNAME = alzhver1_user
PASSWORD = Rf9ZiVs0i9XKxpekiIz5mbHpr0ioJmHi
INTERNAL DATABASE URL = postgresql://alzhver1_user:Rf9ZiVs0i9XKxpekiIz5mbHpr0ioJmHi@dpg-d3ofmnfdiees73b8ko70-a/Alzhver1
EXTERNAL DATABASE URL = postgresql://alzhver1_user:Rf9ZiVs0i9XKxpekiIz5mbHpr0ioJmHi@dpg-d3ofmnfdiees73b8ko70-a.oregon-postgres.render.com/alzhver1

# ACTIVAR MINIO

.\minio.exe server D:\minio --console-address :9001

# BORRAR ANTES DE PRODUCCION

#

# Backend Alzheimer API

Backend desarrollado con FastAPI para la gestión de pacientes con Alzheimer, incluyendo autenticación JWT, gestión de usuarios (pacientes, cuidadores, médicos y admins) y base de datos PostgreSQL.

## 🚀 Características

- ✅ Autenticación JWT
- ✅ Registro y login de usuarios
- ✅ 4 tipos de usuarios: Paciente, Cuidador, Médico, Admin
- ✅ Base de datos PostgreSQL con SQLAlchemy
- ✅ Validación con Pydantic
- ✅ CORS configurado
- ✅ Documentación automática (Swagger/OpenAPI)

## 📋 Requisitos

- Python 3.9+
- PostgreSQL 12+

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
cd BackendAlzheimer
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura tus variables:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/alzheimer_db
SECRET_KEY=tu_clave_secreta_super_segura_cambiala_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Crear la base de datos

Primero, crea la base de datos en PostgreSQL:

```sql
CREATE DATABASE alzheimer_db;
```

Luego ejecuta el script SQL para crear las tablas (el que proporcionaste).

## ▶️ Ejecutar la aplicación

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O simplemente:

```bash
python run.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

Una vez ejecutada la aplicación, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Endpoints de Autenticación

### 1. Registro de Usuario

**POST** `/api/auth/register`

```json
{
  "username": "juan_perez",
  "password": "password123",
  "tipo_usuario": "paciente",
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "telefono": "987654321",
  "fecha_nacimiento": "1950-05-15",
  "genero": "Masculino",
  "numero_identidad": "12345678",
  "ciudad": "Lima"
}
```

### 2. Login

**POST** `/api/auth/login`

```json
{
  "username": "juan_perez",
  "password": "password123"
}
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Obtener Usuario Actual

**GET** `/api/auth/me`

Headers:

```
Authorization: Bearer {token}
```

## 📝 Ejemplos de Registro por Tipo de Usuario

### Paciente

```json
{
  "username": "paciente01",
  "password": "pass123456",
  "tipo_usuario": "paciente",
  "nombre": "María",
  "apellido": "González",
  "email": "maria@example.com",
  "telefono": "987654321",
  "fecha_nacimiento": "1945-03-20",
  "genero": "Femenino",
  "numero_identidad": "87654321",
  "direccion": "Av. Arequipa 123",
  "ciudad": "Lima",
  "estado_alzheimer": "independiente"
}
```

### Cuidador

```json
{
  "username": "cuidador01",
  "password": "pass123456",
  "tipo_usuario": "cuidador",
  "nombre": "Carlos",
  "apellido": "Ramírez",
  "email": "carlos@example.com",
  "telefono": "912345678",
  "relacion_paciente": "Hijo",
  "direccion": "Calle Los Olivos 456"
}
```

### Médico

```json
{
  "username": "doctor01",
  "password": "pass123456",
  "tipo_usuario": "medico",
  "nombre": "Ana",
  "apellido": "Torres",
  "email": "ana.torres@hospital.com",
  "telefono": "998877665",
  "cmp": "12345",
  "especialidad": "Neurología",
  "numero_identidad": "45678912",
  "hospital_afiliacion": "Hospital Nacional"
}
```

### Admin

```json
{
  "username": "admin01",
  "password": "pass123456",
  "tipo_usuario": "admin",
  "nombre": "Luis",
  "apellido": "Mendoza",
  "email": "admin@example.com",
  "telefono": "987654321",
  "nivel_acceso": "total",
  "permisos": "all"
}
```

## 🧪 Probar los Endpoints

### Usando curl:

```bash
# Registro
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "test123456",
    "tipo_usuario": "paciente",
    "nombre": "Test",
    "apellido": "User",
    "email": "test@example.com",
    "fecha_nacimiento": "1950-01-01"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "test123456"
  }'

# Obtener usuario actual (reemplaza TOKEN con el token obtenido)
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer TOKEN"
```

## 🔒 Seguridad

- Las contraseñas se hashean con bcrypt
- Los tokens JWT expiran en 30 minutos (configurable)
- Validación de datos con Pydantic
- CORS configurado para orígenes específicos
