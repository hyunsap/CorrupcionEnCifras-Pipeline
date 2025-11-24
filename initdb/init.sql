-- ============================================
-- Configuración inicial
-- ============================================
SET client_encoding = 'UTF8';
SET timezone = 'America/Argentina/Buenos_Aires';

CREATE SCHEMA IF NOT EXISTS public;

-- ============================================
-- Entidades principales
-- ============================================

-- Fuero
CREATE TABLE fuero (
    fuero_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Jurisdicción
CREATE TABLE jurisdiccion (
    jurisdiccion_id SERIAL PRIMARY KEY,
    ambito VARCHAR(50) NOT NULL,
    departamento_judicial VARCHAR(100)
);

-- Tribunal
CREATE TABLE tribunal (
    tribunal_id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) UNIQUE NOT NULL,
    domicilio_sede TEXT,
    contacto VARCHAR(200),
    fuero VARCHAR(100) NOT NULL,
    jurisdiccion_id INTEGER NOT NULL,
    CONSTRAINT fk_tribunal_jurisdiccion 
        FOREIGN KEY (jurisdiccion_id) REFERENCES jurisdiccion(jurisdiccion_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);


-- Tipo Delito
CREATE TABLE tipo_delito (
    tipo_delito_id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL UNIQUE,
    articulo VARCHAR(50),
    ley VARCHAR(50)
);

-- Letrado
CREATE TABLE letrado (
    letrado_id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL UNIQUE
);

-- ==============================
-- TABLA EXPEDIENTE
-- ==============================
CREATE TABLE expediente (
    numero_expediente VARCHAR(50) PRIMARY KEY,
    caratula TEXT,
    jurisdiccion TEXT,
    tribunal TEXT, 
    estado_procesal VARCHAR(50) CHECK (estado_procesal IN ('En trámite', 'Terminada')),
    fecha_inicio DATE,
    fecha_ultimo_movimiento DATE,
    camara_origen TEXT,
    ano_inicio INT,
    delitos TEXT,
    fiscal TEXT,
    fiscalia TEXT
);

-- ==============================
-- TABLA RESOLUCION
-- ==============================
CREATE TABLE resolucion (
    id_resolucion SERIAL PRIMARY KEY,
    numero_expediente VARCHAR(50) REFERENCES expediente(numero_expediente) ON DELETE CASCADE,
    fecha DATE,
    nombre TEXT,
    link TEXT
);

-- ==============================
-- TABLA RADICACION
-- ==============================
CREATE TABLE radicacion (
    radicacion_id SERIAL PRIMARY KEY,
    numero_expediente VARCHAR(50) NOT NULL,
    orden INTEGER NOT NULL,
    fecha_radicacion DATE,
    tribunal TEXT,
    fiscal_nombre TEXT,
    fiscalia TEXT,
    CONSTRAINT fk_radicacion_expediente 
        FOREIGN KEY (numero_expediente) REFERENCES expediente(numero_expediente)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_radicacion_expediente_orden 
        UNIQUE (numero_expediente, orden),
    CONSTRAINT chk_orden_positivo 
        CHECK (orden > 0)
);

-- ============================================
-- Entidades dependientes y relaciones N:M
-- ============================================

-- Parte
CREATE TABLE parte (
    parte_id SERIAL PRIMARY KEY,
    numero_expediente VARCHAR(50) NOT NULL,
    nombre_razon_social VARCHAR(200),
    CONSTRAINT fk_parte_expediente 
        FOREIGN KEY (numero_expediente) REFERENCES expediente(numero_expediente)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Rol de la parte
CREATE TABLE rol_parte (
    rol_parte_id SERIAL PRIMARY KEY,
    parte_id INTEGER NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    CONSTRAINT fk_rol_parte_parte 
        FOREIGN KEY (parte_id) REFERENCES parte(parte_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Relación N:M entre expediente y tipo de delito
CREATE TABLE expediente_delito (
    numero_expediente VARCHAR(50) NOT NULL,
    tipo_delito_id INTEGER NOT NULL,
    PRIMARY KEY (numero_expediente, tipo_delito_id),
    CONSTRAINT fk_expediente_delito_exp FOREIGN KEY (numero_expediente)
        REFERENCES expediente(numero_expediente)
        ON DELETE CASCADE,
    CONSTRAINT fk_expediente_delito_tipo FOREIGN KEY (tipo_delito_id)
        REFERENCES tipo_delito(tipo_delito_id)
        ON DELETE RESTRICT
);

-- Representación
CREATE TABLE representacion (
    numero_expediente VARCHAR(50) NOT NULL,
    parte_id INTEGER NOT NULL,
    letrado_id INTEGER NOT NULL,
    rol VARCHAR(100),
    PRIMARY KEY (numero_expediente, parte_id, letrado_id),
    CONSTRAINT fk_repr_exp FOREIGN KEY (numero_expediente)
        REFERENCES expediente(numero_expediente)
        ON DELETE CASCADE,
    CONSTRAINT fk_repr_parte FOREIGN KEY (parte_id)
        REFERENCES parte(parte_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_repr_letrado FOREIGN KEY (letrado_id)
        REFERENCES letrado(letrado_id)
        ON DELETE CASCADE
);

-- ============================================
-- Tabla de Jueces/Magistrados
-- ============================================

CREATE TABLE juez (
    juez_id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(50),
    CONSTRAINT uq_juez_nombre UNIQUE (nombre)
);

-- ============================================
-- Tabla intermedia: Relación Tribunal-Juez
-- ============================================

CREATE TABLE tribunal_juez (
    tribunal_id INTEGER NOT NULL,
    juez_id INTEGER NOT NULL,
    cargo VARCHAR(100),
    situacion VARCHAR(50) DEFAULT 'Efectivo' 
        CHECK (situacion IN ('-','Efectivo', 'Efectiva', 'Subrogante', 'Interino', 'Interina', 'Suplente', 'Contratado', 'Contratada', 'Adscripto', 'Adscripta', 'Titular', 'En Comisión', 'En comisión', 'Reemplazante', 'Reemplazanta', 'Ad-hoc', 'Ad hoc', 'Ad honorem', 'Conjuez', 'Vacante', 'Secretario', 'Secretaria', 'Prosecretario', 'Prosecretaria')),
    PRIMARY KEY (tribunal_id, juez_id),
    CONSTRAINT fk_tribunal_juez_tribunal 
        FOREIGN KEY (tribunal_id) REFERENCES tribunal(tribunal_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tribunal_juez_juez 
        FOREIGN KEY (juez_id) REFERENCES juez(juez_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================
-- Índices
-- ============================================
CREATE INDEX idx_expediente_fecha_inicio ON expediente(fecha_inicio);
CREATE INDEX idx_expediente_fecha_ultimo_movimiento ON expediente(fecha_ultimo_movimiento);
CREATE INDEX idx_parte_expediente ON parte(numero_expediente);
CREATE INDEX idx_tribunal_jurisdiccion ON tribunal(jurisdiccion_id);
CREATE INDEX idx_tribunal_juez_tribunal ON tribunal_juez(tribunal_id);
CREATE INDEX idx_tribunal_juez_juez ON tribunal_juez(juez_id);
CREATE INDEX idx_tribunal_juez_cargo ON tribunal_juez(cargo);
CREATE INDEX idx_juez_nombre ON juez(nombre);
CREATE INDEX idx_radicacion_expediente ON radicacion(numero_expediente);
CREATE INDEX idx_radicacion_orden ON radicacion(numero_expediente, orden);
CREATE INDEX idx_radicacion_fecha ON radicacion(fecha_radicacion);
CREATE INDEX idx_expediente_delito_expediente ON expediente_delito(numero_expediente);
CREATE INDEX idx_expediente_delito_tipo ON expediente_delito(tipo_delito_id);
CREATE INDEX idx_tipo_delito_nombre ON tipo_delito(nombre);

-- ============================================
-- Comentarios
-- ============================================
COMMENT ON TABLE expediente IS 'Tabla principal que contiene la información de los expedientes judiciales';
COMMENT ON COLUMN expediente.estado_procesal IS 'Estado procesal textual: En trámite o Terminada';
COMMENT ON TABLE parte IS 'Personas físicas o jurí­dicas involucradas en un expediente';
COMMENT ON TABLE rol_parte IS 'Roles específicos que una parte cumple en un expediente';
COMMENT ON TABLE representacion IS 'Relación entre parte y letrado en un expediente';
COMMENT ON TABLE expediente_delito IS 'Asociación N:M entre expedientes y delitos imputados';
COMMENT ON TABLE resolucion IS 'Resoluciones dictadas en un expediente';
COMMENT ON TABLE radicacion IS 'Historial de radicaciones de cada expediente (movimientos entre tribunales)';
COMMENT ON TABLE juez IS 'Magistrados y jueces que integran tribunales';
COMMENT ON TABLE tribunal_juez IS 'Relación N:M entre tribunales y jueces con información de cargo y situación';

-- ============================================
-- Datos iniciales
-- ============================================
INSERT INTO jurisdiccion (jurisdiccion_id, ambito, departamento_judicial)
VALUES (1, 'Federal', 'Comodoro Py')
ON CONFLICT (jurisdiccion_id) DO NOTHING;

INSERT INTO jurisdiccion (jurisdiccion_id, ambito, departamento_judicial)
VALUES (2, 'Nacional', 'Comodoro Py')
ON CONFLICT (jurisdiccion_id) DO NOTHING;