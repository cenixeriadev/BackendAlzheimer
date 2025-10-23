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
    tipo_usuario VARCHAR(20) NOT NULL CHECK (tipo_usuario IN ('paciente', 'cuidador', 'medico', 'admin', 'ai_agent')),
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
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    medico_id INTEGER REFERENCES medico(id) ON DELETE SET NULL,
    cita_id INTEGER REFERENCES cita(id) ON DELETE SET NULL,
    descripcion TEXT,
    recomendaciones TEXT,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'confirmado', 'revisado')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- NUEVA: Tabla para Segmentación de Imágenes
-- ==========================================
CREATE TABLE imagen_segmentada (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    diagnostico_id INTEGER REFERENCES diagnostico(id) ON DELETE CASCADE,
    imagen_original_url VARCHAR(500) NOT NULL,
    imagen_segmentada_url VARCHAR(500),
    tipo_segmentacion VARCHAR(100) NOT NULL CHECK (tipo_segmentacion IN ('hipocampo', 'ventriculos', 'materia_gris', 'materia_blanca', 'completa', 'personalizada')),
    algoritmo_utilizado VARCHAR(100) NOT NULL DEFAULT 'unet',
    
    -- Métricas de segmentación
    volumen_segmentado_mm3 DECIMAL(10, 2),
    area_segmentada_mm2 DECIMAL(10, 2),
    porcentaje_atrofia DECIMAL(5, 2),
    
    -- Información técnica
    precision_segmentacion DECIMAL(5, 4),
    tiempo_procesamiento_segundos DECIMAL(8, 2),
    
    -- Máscaras y coordenadas
    mascara_binaria_url VARCHAR(500),
    coordenadas_roi JSONB,
    metadata_segmentacion JSONB,
    
    estado_proceso VARCHAR(50) DEFAULT 'procesando' CHECK (estado_proceso IN ('procesando', 'completado', 'fallido', 'en_revision')),
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Resultado_IA (Actualizada con referencia a segmentación)
CREATE TABLE resultado_ia (
    id SERIAL PRIMARY KEY,
    diagnostico_id INTEGER NOT NULL REFERENCES diagnostico(id) ON DELETE CASCADE,
    paciente_id INTEGER NOT NULL REFERENCES paciente(id) ON DELETE CASCADE,
    imagen_original_url VARCHAR(500) NOT NULL,
    imagen_procesada_url VARCHAR(500),
    imagen_segmentada_id INTEGER REFERENCES imagen_segmentada(id) ON DELETE SET NULL,
    fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    clasificacion_principal_id INTEGER NOT NULL REFERENCES clasificacion_resultados(id),
    confianza_principal DECIMAL(5, 4) NOT NULL,
    
    -- Probabilidades de cada clasificación
    probabilidad_no_demented DECIMAL(5, 4),
    probabilidad_very_mild_demented DECIMAL(5, 4),
    probabilidad_mild_demented DECIMAL(5, 4),
    probabilidad_moderate_demented DECIMAL(5, 4),
    
    -- Modelo utilizado
    modelo_ia_version VARCHAR(50) DEFAULT 'cnn_v1',
    
    metadata_procesamiento JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- NUEVO: Sistema de AI Agent y Chat Administrativo
-- ==========================================

-- Tabla: AI_Agent_Config
-- Configuración del agente AI para consultas administrativas
CREATE TABLE ai_agent_config (
    id SERIAL PRIMARY KEY,
    nombre_agente VARCHAR(100) NOT NULL UNIQUE,
    modelo_llm VARCHAR(100) NOT NULL DEFAULT 'claude-3.5-sonnet',
    temperatura DECIMAL(3, 2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4000,
    system_prompt TEXT NOT NULL,
    permisos_acceso JSONB NOT NULL, -- Tablas y operaciones permitidas
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: AI_Agent_Session
-- Sesiones de conversación con el AI Agent
CREATE TABLE ai_agent_session (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    agent_config_id INTEGER NOT NULL REFERENCES ai_agent_config(id) ON DELETE SET NULL,
    titulo_sesion VARCHAR(200),
    estado VARCHAR(50) DEFAULT 'activa' CHECK (estado IN ('activa', 'finalizada', 'pausada')),
    metadata_sesion JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: AI_Agent_Message
-- Mensajes en conversaciones con el AI Agent
CREATE TABLE ai_agent_message (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES ai_agent_session(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('user', 'assistant', 'system')),
    contenido TEXT NOT NULL,
    
    -- Consultas SQL ejecutadas por el agente
    sql_ejecutado TEXT,
    sql_resultados JSONB,
    
    -- Métricas de la consulta
    tiempo_ejecucion_ms INTEGER,
    filas_afectadas INTEGER,
    
    -- Contexto y herramientas usadas
    tools_usados JSONB,
    metadata JSONB,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: AI_Agent_Query_Log
-- Log de todas las consultas realizadas por el AI Agent
CREATE TABLE ai_agent_query_log (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES ai_agent_session(id) ON DELETE CASCADE,
    admin_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    consulta_original TEXT NOT NULL,
    sql_generado TEXT NOT NULL,
    sql_ejecutado TEXT NOT NULL,
    
    -- Resultado de la ejecución
    estado_ejecucion VARCHAR(50) NOT NULL CHECK (estado_ejecucion IN ('exitoso', 'error', 'timeout', 'cancelado')),
    resultado_json JSONB,
    error_mensaje TEXT,
    
    -- Métricas
    tiempo_generacion_ms INTEGER,
    tiempo_ejecucion_ms INTEGER,
    filas_retornadas INTEGER,
    
    -- Seguridad y auditoría
    tablas_accedidas TEXT[],
    operacion_tipo VARCHAR(20) CHECK (operacion_tipo IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'ANALYTICS')),
    requiere_revision BOOLEAN DEFAULT FALSE,
    revisado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: AI_Agent_Analytics
-- Métricas y analytics del uso del AI Agent
CREATE TABLE ai_agent_analytics (
    id SERIAL PRIMARY KEY,
    agent_config_id INTEGER REFERENCES ai_agent_config(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    
    -- Métricas de uso
    total_consultas INTEGER DEFAULT 0,
    consultas_exitosas INTEGER DEFAULT 0,
    consultas_fallidas INTEGER DEFAULT 0,
    tiempo_promedio_respuesta_ms INTEGER,
    
    -- Métricas de datos
    tablas_mas_consultadas JSONB,
    tipos_consultas JSONB,
    
    -- Costos (si aplica)
    tokens_consumidos INTEGER,
    costo_estimado DECIMAL(10, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_config_id, fecha)
);

-- Tabla: Mensaje_Chat (Actualizada para médico-paciente)
CREATE TABLE mensaje_chat (
    id SERIAL PRIMARY KEY,
    cita_id INTEGER NOT NULL REFERENCES cita(id) ON DELETE CASCADE,
    usuario_remitente_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE SET NULL,
    contenido TEXT NOT NULL,
    archivo_url VARCHAR(500),
    tipo_mensaje VARCHAR(50) DEFAULT 'texto' CHECK (tipo_mensaje IN ('texto', 'imagen', 'documento', 'audio', 'resultado_ia')),
    leido BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Auditoria (Actualizada)
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    tipo_actor VARCHAR(20) DEFAULT 'usuario' CHECK (tipo_actor IN ('usuario', 'ai_agent', 'sistema')),
    tabla_afectada VARCHAR(100) NOT NULL,
    tipo_operacion VARCHAR(20) NOT NULL CHECK (tipo_operacion IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT')),
    registro_id INTEGER,
    cambios JSONB,
    ip_origen VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- VISTAS PARA EL AI AGENT
-- ==========================================

-- Vista: Resumen de pacientes para consultas del AI Agent
CREATE OR REPLACE VIEW v_pacientes_resumen AS
SELECT 
    p.id,
    p.nombre,
    p.apellido,
    p.fecha_nacimiento,
    EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) as edad,
    p.genero,
    p.estado_alzheimer,
    COUNT(DISTINCT d.id) as total_diagnosticos,
    COUNT(DISTINCT r.id) as total_analisis_ia,
    COUNT(DISTINCT seg.id) as total_segmentaciones,
    MAX(d.fecha_emision) as ultimo_diagnostico,
    c.nombre as nombre_cuidador,
    c.apellido as apellido_cuidador
FROM paciente p
LEFT JOIN diagnostico d ON p.id = d.paciente_id
LEFT JOIN resultado_ia r ON p.id = r.paciente_id
LEFT JOIN imagen_segmentada seg ON p.id = seg.paciente_id
LEFT JOIN cuidador c ON p.cuidador_id = c.usuario_id
GROUP BY p.id, c.nombre, c.apellido;

-- Vista: Estadísticas de resultados IA
CREATE OR REPLACE VIEW v_estadisticas_ia AS
SELECT 
    cr.nombre_espanol as clasificacion,
    COUNT(r.id) as total_casos,
    AVG(r.confianza_principal) as confianza_promedio,
    MIN(r.confianza_principal) as confianza_minima,
    MAX(r.confianza_principal) as confianza_maxima
FROM resultado_ia r
JOIN clasificacion_resultados cr ON r.clasificacion_principal_id = cr.id
GROUP BY cr.nombre_espanol;

-- Vista: Estadísticas de segmentación
CREATE OR REPLACE VIEW v_estadisticas_segmentacion AS
SELECT 
    tipo_segmentacion,
    COUNT(*) as total_segmentaciones,
    AVG(volumen_segmentado_mm3) as volumen_promedio,
    AVG(porcentaje_atrofia) as atrofia_promedio,
    AVG(precision_segmentacion) as precision_promedio,
    AVG(tiempo_procesamiento_segundos) as tiempo_promedio
FROM imagen_segmentada
WHERE estado_proceso = 'completado'
GROUP BY tipo_segmentacion;

-- Vista: Dashboard para administradores
CREATE OR REPLACE VIEW v_dashboard_admin AS
SELECT 
    (SELECT COUNT(*) FROM paciente) as pacientes_activos,
    (SELECT COUNT(*) FROM medico) as medicos_totales,
    (SELECT COUNT(*) FROM cita WHERE fecha_hora >= CURRENT_DATE) as citas_pendientes,
    (SELECT COUNT(*) FROM diagnostico WHERE estado = 'pendiente') as diagnosticos_pendientes,
    (SELECT COUNT(*) FROM resultado_ia WHERE DATE(fecha_analisis) = CURRENT_DATE) as analisis_hoy,
    (SELECT COUNT(*) FROM imagen_segmentada WHERE estado_proceso = 'procesando') as segmentaciones_proceso;

-- ==========================================
-- ÍNDICES OPTIMIZADOS
-- ==========================================

-- Índices existentes
CREATE INDEX IF NOT EXISTS idx_usuario_username ON usuario(username);
CREATE INDEX IF NOT EXISTS idx_usuario_tipo ON usuario(tipo_usuario);
CREATE INDEX IF NOT EXISTS idx_usuario_estado ON usuario(estado);
CREATE INDEX IF NOT EXISTS idx_paciente_usuario_id ON paciente(usuario_id);
CREATE INDEX IF NOT EXISTS idx_paciente_cuidador_id ON paciente(cuidador_id);
CREATE INDEX IF NOT EXISTS idx_medico_usuario_id ON medico(usuario_id);
CREATE INDEX IF NOT EXISTS idx_medico_cmp ON medico(cmp);
CREATE INDEX IF NOT EXISTS idx_cita_paciente_id ON cita(paciente_id);
CREATE INDEX IF NOT EXISTS idx_cita_medico_id ON cita(medico_id);
CREATE INDEX IF NOT EXISTS idx_cita_fecha_hora ON cita(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_diagnostico_paciente_id ON diagnostico(paciente_id);
CREATE INDEX IF NOT EXISTS idx_resultado_ia_paciente_id ON resultado_ia(paciente_id);
CREATE INDEX IF NOT EXISTS idx_resultado_ia_diagnostico_id ON resultado_ia(diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_resultado_ia_fecha ON resultado_ia(fecha_analisis);
CREATE INDEX IF NOT EXISTS idx_mensaje_chat_cita_id ON mensaje_chat(cita_id);

-- Nuevos índices para AI Agent y segmentación
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_paciente_id ON imagen_segmentada(paciente_id);
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_diagnostico_id ON imagen_segmentada(diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_tipo ON imagen_segmentada(tipo_segmentacion);
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_estado ON imagen_segmentada(estado_proceso);
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_fecha ON imagen_segmentada(fecha_procesamiento);

CREATE INDEX IF NOT EXISTS idx_ai_session_admin_id ON ai_agent_session(admin_id);
CREATE INDEX IF NOT EXISTS idx_ai_session_estado ON ai_agent_session(estado);
CREATE INDEX IF NOT EXISTS idx_ai_message_session_id ON ai_agent_message(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_message_timestamp ON ai_agent_message(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_query_log_session_id ON ai_agent_query_log(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_query_log_admin_id ON ai_agent_query_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_ai_query_log_timestamp ON ai_agent_query_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_query_log_estado ON ai_agent_query_log(estado_ejecucion);

CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_id ON auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_tipo_actor ON auditoria(tipo_actor);
CREATE INDEX IF NOT EXISTS idx_auditoria_timestamp ON auditoria(timestamp);

-- Índices JSONB para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_resultado_ia_metadata ON resultado_ia USING GIN (metadata_procesamiento);
CREATE INDEX IF NOT EXISTS idx_imagen_segmentada_metadata ON imagen_segmentada USING GIN (metadata_segmentacion);
CREATE INDEX IF NOT EXISTS idx_ai_query_log_resultado ON ai_agent_query_log USING GIN (resultado_json);

-- ==========================================
-- FUNCIONES PARA SEGURIDAD DEL AI AGENT
-- ==========================================

-- Función: Validar que el AI Agent solo ejecute SELECTs seguros
CREATE OR REPLACE FUNCTION validar_query_ai_agent(sql_query TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Convertir a minúsculas para análisis
    sql_query := LOWER(TRIM(sql_query));
    
    -- Solo permitir SELECT
    IF sql_query !~ '^select' THEN
        RETURN FALSE;
    END IF;
    
    -- Prohibir comandos peligrosos
    IF sql_query ~* '(drop|truncate|delete|insert|update|alter|create|grant|revoke)' THEN
        RETURN FALSE;
    END IF;
    
    -- Prohibir funciones del sistema
    IF sql_query ~* '(pg_sleep|pg_read_file|copy|lo_import|lo_export)' THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Función: Registrar consulta del AI Agent
CREATE OR REPLACE FUNCTION registrar_consulta_ai_agent(
    p_session_id INTEGER,
    p_admin_id INTEGER,
    p_consulta_original TEXT,
    p_sql_generado TEXT,
    p_resultado JSONB,
    p_tiempo_ms INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_query_log_id INTEGER;
    v_tablas TEXT[];
BEGIN
    -- Extraer tablas accedidas (simplificado)
    v_tablas := ARRAY(
        SELECT DISTINCT unnest(
            regexp_matches(p_sql_generado, 'FROM\s+([a-z_]+)', 'gi')
        )
    );
    
    INSERT INTO ai_agent_query_log (
        session_id,
        admin_id,
        consulta_original,
        sql_generado,
        sql_ejecutado,
        estado_ejecucion,
        resultado_json,
        tiempo_ejecucion_ms,
        filas_retornadas,
        tablas_accedidas,
        operacion_tipo
    ) VALUES (
        p_session_id,
        p_admin_id,
        p_consulta_original,
        p_sql_generado,
        p_sql_generado,
        'exitoso',
        p_resultado,
        p_tiempo_ms,
        jsonb_array_length(p_resultado),
        v_tablas,
        'SELECT'
    ) RETURNING id INTO v_query_log_id;
    
    RETURN v_query_log_id;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- DATOS INICIALES
-- ==========================================

-- Clasificaciones de resultados
INSERT INTO clasificacion_resultados (class_id, nombre_ingles, nombre_espanol, descripcion) VALUES
(2, 'Non_Demented', 'Sin Demencia', 'No hay indicios de demencia detectados'),
(3, 'Very_Mild_Demented', 'Demencia Muy Leve', 'Síntomas muy leves de demencia'),
(0, 'Mild_Demented', 'Demencia Leve', 'Demencia en estadio leve'),
(1, 'Moderate_Demented', 'Demencia Moderada', 'Demencia en estadio moderado')
ON CONFLICT (class_id) DO NOTHING;

-- Configuración inicial del AI Agent
INSERT INTO ai_agent_config (
    nombre_agente,
    modelo_llm,
    system_prompt,
    permisos_acceso
) VALUES (
    'AdminAssistant',
    'claude-3.5-sonnet',
    'Eres un asistente especializado en análisis de datos médicos para una aplicación de detección de Alzheimer. Puedes consultar la base de datos para proporcionar estadísticas, reportes y análisis. Siempre genera consultas SQL seguras (solo SELECT) y presenta los resultados de forma clara y profesional.',
    '{
        "tablas_permitidas": ["paciente", "diagnostico", "resultado_ia", "imagen_segmentada", "cita", "medico", "hospital"],
        "vistas_permitidas": ["v_pacientes_resumen", "v_estadisticas_ia", "v_estadisticas_segmentacion", "v_dashboard_admin"],
        "operaciones": ["SELECT"],
        "max_rows": 1000
    }'::jsonb
)
ON CONFLICT (nombre_agente) DO NOTHING;

-- ==========================================
-- COMENTARIOS EN TABLAS
-- ==========================================

COMMENT ON TABLE imagen_segmentada IS 'Almacena resultados de segmentación de imágenes MRI con métricas volumétricas';
COMMENT ON TABLE ai_agent_config IS 'Configuración de agentes AI para consultas administrativas vía MCP';
COMMENT ON TABLE ai_agent_session IS 'Sesiones de conversación entre administradores y AI agents';
COMMENT ON TABLE ai_agent_message IS 'Mensajes y consultas SQL ejecutadas por AI agents';
COMMENT ON TABLE ai_agent_query_log IS 'Log completo de todas las consultas SQL generadas por AI agents';
COMMENT ON TABLE ai_agent_analytics IS 'Métricas agregadas del uso y rendimiento de AI agents';