-- ==========================================
-- BD PARA APP DETECCIÓN DE ALZHEIMER
-- Con soporte para AI Agent MCP y Segmentación de Imágenes
-- ==========================================

-- Tabla: Usuario
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    foto_perfil_url VARCHAR(500),
    tipo_usuario VARCHAR(20) NOT NULL CHECK (tipo_usuario IN ('paciente','cuidador', 'medico', 'admin')),
    estado BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Paciente
CREATE TABLE paciente (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero VARCHAR(20),
    numero_identidad VARCHAR(20) UNIQUE,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    ciudad VARCHAR(100),
    estado_alzheimer VARCHAR(50) CHECK (estado_alzheimer IN ('independiente', 'con_cuidador')),
    cuidador_id INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    notas_medicas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Cuidador
CREATE TABLE cuidador (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    relacion_paciente VARCHAR(50) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Medico
CREATE TABLE medico (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    cmp VARCHAR(20) NOT NULL UNIQUE,
    especialidad VARCHAR(100),
    numero_identidad VARCHAR(20) UNIQUE,
    telefono VARCHAR(20),
    email VARCHAR(100),
    hospital_afiliacion VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Admin
CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    nivel_acceso VARCHAR(50) DEFAULT 'total' CHECK (nivel_acceso IN ('total', 'limitado')),
    permisos TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Clasificacion_Resultados
CREATE TABLE clasificacion_resultados (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL UNIQUE,
    nombre_ingles VARCHAR(100) NOT NULL,
    nombre_espanol VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Hospital
CREATE TABLE hospital (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL UNIQUE,
    ciudad VARCHAR(100),
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Tabla: Cita
CREATE TABLE cita (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    medico_id INTEGER NOT NULL REFERENCES medico(id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES hospital(id) ON DELETE SET NULL,
    fecha_hora TIMESTAMP NOT NULL,
    estado VARCHAR(50) DEFAULT 'programada' CHECK (estado IN ('programada', 'completada', 'cancelada', 'reprogramada')),
    motivo TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Diagnostico
CREATE TABLE diagnostico (
    -- Clave Primaria y de Índice
    id SERIAL PRIMARY KEY,
    
    -- Clave Foránea
    paciente_id INTEGER NOT NULL REFERENCES usuario(id),
    
    -- Campos del Diagnóstico
    resultado VARCHAR(255),
    confianza REAL, -- 'REAL' es el tipo de coma flotante de precisión simple (Float)
    clase_original VARCHAR(255),
    
    -- URLs de Imágenes
    imagen_original_url VARCHAR(255),
    imagen_procesada_url VARCHAR(255),
    
    -- Datos Estructurados
    datos_roboflow JSONB, -- 'JSONB' es más eficiente y preferible para datos JSON en PostgreSQL
    
    -- Campos de Control
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'completado'
);

-- Clasificaciones de resultados
INSERT INTO clasificacion_resultados (class_id, nombre_ingles, nombre_espanol, descripcion) VALUES
(2, 'Non_Demented', 'Sin Demencia', 'No hay indicios de demencia detectados'),
(3, 'Very_Mild_Demented', 'Demencia Muy Leve', 'Síntomas muy leves de demencia'),
(0, 'Mild_Demented', 'Demencia Leve', 'Demencia en estadio leve'),
(1, 'Moderate_Demented', 'Demencia Moderada', 'Demencia en estadio moderado')
ON CONFLICT (class_id) DO NOTHING;
