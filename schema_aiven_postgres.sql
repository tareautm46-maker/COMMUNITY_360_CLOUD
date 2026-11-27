-- =============================================================================
-- ESQUEMA DDL PARA POSTGRESQL (AIVEN CLOUD) - PROYECTO COMMUNITY 360 (FASE 2)
-- =============================================================================

-- 1. Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario VARCHAR(20) PRIMARY KEY,
    alias VARCHAR(60) NOT NULL,
    fecha_ingreso DATE NOT NULL,
    zona_horaria VARCHAR(50) NOT NULL,
    rango_edad VARCHAR(20) NOT NULL,
    especie_fursona VARCHAR(50) NOT NULL,
    interes_principal VARCHAR(60) NOT NULL,
    plataforma_principal VARCHAR(40) NOT NULL,
    es_artista BOOLEAN NOT NULL DEFAULT FALSE,
    mensajes_30d INT NOT NULL DEFAULT 0,
    reacciones_30d INT NOT NULL DEFAULT 0,
    eventos_asistidos INT NOT NULL DEFAULT 0,
    comisiones_compradas INT NOT NULL DEFAULT 0,
    sentimiento_promedio NUMERIC(5,3) NOT NULL,
    ultima_actividad DATE NOT NULL,
    estatus VARCHAR(20) NOT NULL,
    consentimiento_datos BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usuarios_estatus ON usuarios (estatus);
CREATE INDEX IF NOT EXISTS idx_usuarios_consentimiento ON usuarios (consentimiento_datos);

-- 2. Tabla: ubicaciones_usuario (Cumplimiento Privacy by Design)
CREATE TABLE IF NOT EXISTS ubicaciones_usuario (
    id_ubicacion SERIAL PRIMARY KEY,
    id_usuario VARCHAR(20) NOT NULL UNIQUE,
    pais VARCHAR(60) NOT NULL,
    estado VARCHAR(60) NOT NULL,
    ciudad VARCHAR(80) NOT NULL,
    latitud NUMERIC(9,6),
    longitud NUMERIC(9,6),
    CONSTRAINT fk_ubicaciones_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
);

-- 3. Tabla: interacciones (Interacciones validadas y vinculadas)
CREATE TABLE IF NOT EXISTS interacciones (
    id_interaccion VARCHAR(20) PRIMARY KEY,
    id_usuario VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    canal VARCHAR(40) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    texto TEXT,
    tema VARCHAR(50) NOT NULL,
    sentimiento NUMERIC(4,2) NOT NULL,
    idioma VARCHAR(15) NOT NULL,
    dispositivo VARCHAR(30) NOT NULL,
    longitud_texto INT NOT NULL DEFAULT 0,
    reacciones_recibidas INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_interacciones_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE INDEX IF NOT EXISTS idx_interacciones_usuario_fecha ON interacciones (id_usuario, timestamp);
CREATE INDEX IF NOT EXISTS idx_interacciones_canal ON interacciones (canal);
CREATE INDEX IF NOT EXISTS idx_interacciones_tema ON interacciones (tema);

-- 4. Tabla: interacciones_no_vinculadas (Aislamiento de huérfanos/anomalías)
CREATE TABLE IF NOT EXISTS interacciones_no_vinculadas (
    id_registro SERIAL PRIMARY KEY,
    id_interaccion VARCHAR(20) NOT NULL,
    id_usuario_origen VARCHAR(60),
    timestamp TIMESTAMP NOT NULL,
    canal VARCHAR(40) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    texto TEXT,
    tema VARCHAR(50) NOT NULL,
    sentimiento NUMERIC(4,2) NOT NULL,
    idioma VARCHAR(15) NOT NULL,
    dispositivo VARCHAR(30) NOT NULL,
    longitud_texto INT NOT NULL DEFAULT 0,
    reacciones_recibidas INT NOT NULL DEFAULT 0,
    etiquetas_raw VARCHAR(255),
    motivo_aislamiento VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_no_vinculadas_usuario_origen ON interacciones_no_vinculadas (id_usuario_origen);
CREATE INDEX IF NOT EXISTS idx_no_vinculadas_timestamp ON interacciones_no_vinculadas (timestamp);

-- 5. Tabla: etiquetas (Catálogo normalizado)
CREATE TABLE IF NOT EXISTS etiquetas (
    id_etiqueta SERIAL PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL UNIQUE
);

-- 6. Tabla: interaccion_etiquetas (Relación N:M)
CREATE TABLE IF NOT EXISTS interaccion_etiquetas (
    id_interaccion VARCHAR(20) NOT NULL,
    id_etiqueta INT NOT NULL,
    PRIMARY KEY (id_interaccion, id_etiqueta),
    CONSTRAINT fk_ie_interaccion
        FOREIGN KEY (id_interaccion) REFERENCES interacciones(id_interaccion)
        ON DELETE CASCADE,
    CONSTRAINT fk_ie_etiqueta
        FOREIGN KEY (id_etiqueta) REFERENCES etiquetas(id_etiqueta)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interaccion_etiquetas_etiqueta ON interaccion_etiquetas (id_etiqueta);
