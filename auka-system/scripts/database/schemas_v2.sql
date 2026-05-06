-- ============================================================
-- AUKA SYSTEM - ESQUEMA DE BASE DE DATOS V2 (Nombres únicos)
-- Ejecutar en: Supabase SQL Editor
-- ============================================================

-- Tabla principal de prospectos
CREATE TABLE IF NOT EXISTS auka_prospectos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa TEXT,
    evento TEXT,
    tipo_evento TEXT,
    fecha DATE,
    ubicacion TEXT,
    ciudad TEXT,
    lat FLOAT,
    lng FLOAT,
    telefono TEXT,
    email TEXT,
    web TEXT,
    instagram TEXT,
    estado TEXT DEFAULT 'nuevo', -- nuevo/contactado/pendiente/cerrado
    prioridad TEXT DEFAULT 'BAJA', -- ALTA/MEDIA/BAJA
    score INT DEFAULT 0,
    notas TEXT,
    fuente TEXT, -- google_maps/instagram/web
    raw_data JSONB,
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT valid_ciudad CHECK (ciudad IN ('Caracas', 'Valencia', 'Maracay', 'La Guaira', NULL)),
    CONSTRAINT valid_tipo CHECK (tipo_evento IN ('deportivo', 'corporativo', 'social', 'cultural', 'gastronomico', 'religioso', 'otro', NULL)),
    CONSTRAINT valid_estado CHECK (estado IN ('nuevo', 'contactado', 'pendiente', 'cerrado')),
    CONSTRAINT valid_prioridad CHECK (prioridad IN ('ALTA', 'MEDIA', 'BAJA'))
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_ciudad ON auka_prospectos(ciudad);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_prioridad ON auka_prospectos(prioridad);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_tipo_evento ON auka_prospectos(tipo_evento);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_estado ON auka_prospectos(estado);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_score ON auka_prospectos(score DESC);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_creado ON auka_prospectos(creado_en DESC);
CREATE INDEX IF NOT EXISTS idx_auka_prospectos_empresa ON auka_prospectos(empresa);

-- Tabla de memoria de búsquedas
CREATE TABLE IF NOT EXISTS auka_memoria_busquedas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    fuente TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT NOW(),
    resultados_totales INT DEFAULT 0,
    prospectos_nuevos INT DEFAULT 0,
    duracion_segundos INT DEFAULT 0,
    eficiencia FLOAT DEFAULT 0,
    ciudad TEXT,
    
    CONSTRAINT valid_fuente CHECK (fuente IN ('google_maps', 'instagram', 'web'))
);

CREATE INDEX IF NOT EXISTS idx_auka_memoria_busquedas_fecha ON auka_memoria_busquedas(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_auka_memoria_busquedas_ciudad ON auka_memoria_busquedas(ciudad);
CREATE INDEX IF NOT EXISTS idx_auka_memoria_busquedas_query ON auka_memoria_busquedas(query);

-- Tabla de memoria de empresas (anti-duplicados)
CREATE TABLE IF NOT EXISTS auka_memoria_empresas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa TEXT,
    telefono TEXT,
    instagram TEXT,
    web TEXT,
    hash_identificador TEXT UNIQUE NOT NULL,
    primera_vez_visto TIMESTAMP DEFAULT NOW(),
    ultima_vez_visto TIMESTAMP DEFAULT NOW(),
    veces_encontrado INT DEFAULT 1,
    procesado BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_auka_memoria_empresas_hash ON auka_memoria_empresas(hash_identificador);
CREATE INDEX IF NOT EXISTS idx_auka_memoria_empresas_procesado ON auka_memoria_empresas(procesado);

-- Tabla de rendimiento por fuente
CREATE TABLE IF NOT EXISTS auka_memoria_fuentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente TEXT UNIQUE NOT NULL,
    total_busquedas INT DEFAULT 0,
    total_prospectos INT DEFAULT 0,
    eficiencia_promedio FLOAT DEFAULT 0,
    ultima_busqueda TIMESTAMP,
    activa BOOLEAN DEFAULT true
);

-- Tabla de contexto conversacional
CREATE TABLE IF NOT EXISTS auka_conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    canal TEXT DEFAULT 'telegram',
    mensaje_usuario TEXT,
    respuesta_agente TEXT,
    accion_ejecutada TEXT,
    datos JSONB,
    creado_en TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auka_conversaciones_user ON auka_conversaciones(user_id);
CREATE INDEX IF NOT EXISTS idx_auka_conversaciones_fecha ON auka_conversaciones(creado_en DESC);

-- Vista de prospectos de alta prioridad
CREATE OR REPLACE VIEW auka_prospectos_alta_prioridad AS
SELECT * FROM auka_prospectos 
WHERE prioridad = 'ALTA' AND estado = 'nuevo'
ORDER BY score DESC;

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_auka_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger de actualización automática
DROP TRIGGER IF EXISTS update_auka_prospectos_updated_at ON auka_prospectos;
CREATE TRIGGER update_auka_prospectos_updated_at
    BEFORE UPDATE ON auka_prospectos
    FOR EACH ROW
    EXECUTE FUNCTION update_auka_updated_at_column();

-- Insertar fuentes iniciales
INSERT INTO auka_memoria_fuentes (fuente) VALUES ('google_maps'), ('instagram'), ('web')
ON CONFLICT (fuente) DO NOTHING;
