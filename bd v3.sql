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
    tipo_usuario VARCHAR(20) NOT NULL CHECK (tipo_usuario IN ('paciente', 'medico', 'admin')),
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
    estado_alzheimer VARCHAR(50) CHECK (estado_alzheimer IN ('independiente', 'dependiente')),
    notas_medicas TEXT,
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
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES usuario(id),
    
    resultado VARCHAR(255),
    confianza REAL,
    clase_original VARCHAR(255),
    imagen_original_url VARCHAR(255),
    imagen_procesada_url VARCHAR(255),    
    datos_roboflow JSONB, 
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


-- Tabla: Asignación Médico-Paciente
CREATE TABLE asignacion_medico_paciente (
    id SERIAL PRIMARY KEY,
    medico_id INTEGER NOT NULL REFERENCES medico(id) ON DELETE CASCADE,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(medico_id, paciente_id)
);


INSERT INTO hospital (nombre, ciudad, direccion, telefono) VALUES
('Hospital Nacional', 'Lima', 'Av. Brasil 1000', '01-1234567'),
('Clínica Internacional', 'Lima', 'Av. Salaverry 1000', '01-7654321'),
('Hospital Loayza', 'Lima', 'Av. Alfonso Ugarte 800', '01-9876543')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO cita (paciente_id, medico_id, hospital_id, fecha_hora, estado, motivo) VALUES
(1, 1, 1, '2024-01-15 10:00:00', 'completada', 'Consulta de seguimiento'),
(1, 1, 2, '2024-01-20 14:30:00', 'programada', 'Revisión de resultados')
ON CONFLICT DO NOTHING;

-- ==========================================
-- VISTAS PARA DASHBOARD ADMINISTRATIVO
-- ==========================================

-- Vista: Estadísticas generales del sistema
CREATE OR REPLACE VIEW vista_estadisticas_generales AS
SELECT 
    (SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'paciente' AND estado = TRUE) as total_pacientes_activos,
    (SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'medico' AND estado = TRUE) as total_medicos_activos,
    (SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'admin' AND estado = TRUE) as total_admins_activos,
    (SELECT COUNT(*) FROM usuario WHERE estado = TRUE) as total_usuarios_activos,
    (SELECT COUNT(*) FROM cita WHERE estado = 'programada') as citas_programadas,
    (SELECT COUNT(*) FROM cita WHERE estado = 'completada') as citas_completadas,
    (SELECT COUNT(*) FROM cita WHERE estado = 'cancelada') as citas_canceladas,
    (SELECT COUNT(*) FROM diagnostico) as total_diagnosticos,
    (SELECT COUNT(*) FROM hospital) as total_hospitales,
    (SELECT COUNT(*) FROM asignacion_medico_paciente) as total_asignaciones;

-- Vista: Distribución de diagnósticos por clasificación
CREATE OR REPLACE VIEW vista_diagnosticos_por_clasificacion AS
SELECT 
    cr.nombre_espanol as clasificacion,
    cr.nombre_ingles as clasificacion_ingles,
    COUNT(d.id) as cantidad_diagnosticos,
    ROUND(AVG(d.confianza)::numeric, 2) as confianza_promedio,
    COUNT(DISTINCT d.paciente_id) as pacientes_unicos
FROM diagnostico d
LEFT JOIN clasificacion_resultados cr ON d.clase_original = cr.nombre_ingles
GROUP BY cr.nombre_espanol, cr.nombre_ingles, cr.class_id
ORDER BY cr.class_id;

-- Vista: Actividad de citas por estado y hospital
CREATE OR REPLACE VIEW vista_citas_por_hospital AS
SELECT 
    h.nombre as hospital,
    h.ciudad,
    COUNT(c.id) as total_citas,
    COUNT(CASE WHEN c.estado = 'programada' THEN 1 END) as citas_programadas,
    COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) as citas_completadas,
    COUNT(CASE WHEN c.estado = 'cancelada' THEN 1 END) as citas_canceladas,
    COUNT(CASE WHEN c.estado = 'reprogramada' THEN 1 END) as citas_reprogramadas
FROM hospital h
LEFT JOIN cita c ON h.id = c.hospital_id
GROUP BY h.id, h.nombre, h.ciudad
ORDER BY total_citas DESC;

-- Vista: Detalle de pacientes con información de diagnósticos
CREATE OR REPLACE VIEW vista_pacientes_detallada AS
SELECT 
    p.id as paciente_id,
    p.nombre,
    p.apellido,
    p.fecha_nacimiento,
    EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) as edad,
    p.genero,
    p.ciudad,
    p.estado_alzheimer,
    u.username,
    u.estado as usuario_activo,
    COUNT(DISTINCT d.id) as total_diagnosticos,
    COUNT(DISTINCT c.id) as total_citas,
    COUNT(DISTINCT amp.medico_id) as medicos_asignados,
    MAX(d.created_at) as ultimo_diagnostico,
    MAX(c.fecha_hora) as ultima_cita
FROM paciente p
INNER JOIN usuario u ON p.usuario_id = u.id
LEFT JOIN diagnostico d ON u.id = d.paciente_id
LEFT JOIN cita c ON p.id = c.paciente_id
LEFT JOIN asignacion_medico_paciente amp ON p.id = amp.paciente_id
GROUP BY p.id, p.nombre, p.apellido, p.fecha_nacimiento, p.genero, p.ciudad, p.estado_alzheimer, u.username, u.estado;

-- Vista: Médicos con estadísticas de trabajo
CREATE OR REPLACE VIEW vista_medicos_estadisticas AS
SELECT 
    m.id as medico_id,
    m.nombre,
    m.apellido,
    m.cmp,
    m.especialidad,
    m.hospital_afiliacion,
    u.username,
    u.estado as usuario_activo,
    COUNT(DISTINCT c.id) as total_citas,
    COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) as citas_completadas,
    COUNT(CASE WHEN c.estado = 'programada' THEN 1 END) as citas_programadas,
    COUNT(DISTINCT amp.paciente_id) as pacientes_asignados,
    MAX(c.fecha_hora) as ultima_cita,
    MIN(c.fecha_hora) FILTER (WHERE c.estado = 'programada' AND c.fecha_hora > CURRENT_TIMESTAMP) as proxima_cita
FROM medico m
INNER JOIN usuario u ON m.usuario_id = u.id
LEFT JOIN cita c ON m.id = c.medico_id
LEFT JOIN asignacion_medico_paciente amp ON m.id = amp.medico_id
GROUP BY m.id, m.nombre, m.apellido, m.cmp, m.especialidad, m.hospital_afiliacion, u.username, u.estado;

-- Vista: Actividad reciente del sistema
CREATE OR REPLACE VIEW vista_actividad_reciente AS
SELECT 
    'diagnostico' as tipo_evento,
    d.id as evento_id,
    d.paciente_id as usuario_id,
    d.resultado as detalle,
    d.created_at as fecha_evento
FROM diagnostico d
UNION ALL
SELECT 
    'cita' as tipo_evento,
    c.id as evento_id,
    c.paciente_id as usuario_id,
    CONCAT(c.estado, ' - ', c.motivo) as detalle,
    c.created_at as fecha_evento
FROM cita c
UNION ALL
SELECT 
    'usuario' as tipo_evento,
    u.id as evento_id,
    u.id as usuario_id,
    CONCAT('Usuario ', u.tipo_usuario, ': ', u.username) as detalle,
    u.created_at as fecha_evento
FROM usuario u
ORDER BY fecha_evento DESC
LIMIT 100;

-- Vista: Resumen de diagnósticos por mes
CREATE OR REPLACE VIEW vista_diagnosticos_por_mes AS
SELECT 
    DATE_TRUNC('month', d.created_at) as mes,
    COUNT(d.id) as total_diagnosticos,
    COUNT(DISTINCT d.paciente_id) as pacientes_unicos,
    ROUND(AVG(d.confianza)::numeric, 2) as confianza_promedio,
    COUNT(CASE WHEN cr.nombre_ingles = 'Non_Demented' THEN 1 END) as sin_demencia,
    COUNT(CASE WHEN cr.nombre_ingles = 'Very_Mild_Demented' THEN 1 END) as demencia_muy_leve,
    COUNT(CASE WHEN cr.nombre_ingles = 'Mild_Demented' THEN 1 END) as demencia_leve,
    COUNT(CASE WHEN cr.nombre_ingles = 'Moderate_Demented' THEN 1 END) as demencia_moderada
FROM diagnostico d
LEFT JOIN clasificacion_resultados cr ON d.clase_original = cr.nombre_ingles
GROUP BY DATE_TRUNC('month', d.created_at)
ORDER BY mes DESC;

-- Vista: Dashboard principal consolidado
CREATE OR REPLACE VIEW vista_dashboard_principal AS
SELECT 
    (SELECT row_to_json(eg.*) FROM vista_estadisticas_generales eg) as estadisticas_generales,
    (SELECT json_agg(row_to_json(dpc.*)) FROM vista_diagnosticos_por_clasificacion dpc) as diagnosticos_clasificacion,
    (SELECT json_agg(row_to_json(cph.*)) FROM vista_citas_por_hospital cph) as citas_por_hospital;