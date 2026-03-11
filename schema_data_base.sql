-- SISTEMA DE GESTIÓN DE ALQUILER DE DISFRACES
-- Base de datos para Supabase/PostgreSQL
-- Versión 3.0 - DDL Actualizado
-- 
-- CAMBIOS APLICADOS:
-- 1. Columna 'deposito' eliminada de tabla 'disfraces'
-- 2. Columna 'deposito_requerido' agregada a tabla 'alquileres'
-- 3. Default de 'estado_conservacion' cambiado de 'Bueno' a 'Nuevo'

-- TABLA: clientes
-- Almacena información de los clientes que alquilan disfraces
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- UUID para escalabilidad y compatibilidad con Supabase
    
    nombre VARCHAR(100) NOT NULL,
    -- Nombre completo del cliente
    
    apellido VARCHAR(100) NOT NULL,
    -- Apellido del cliente para búsquedas más eficientes
    
    email VARCHAR(255) UNIQUE,
    -- Email único, útil para notificaciones y login futuro
    
    telefono VARCHAR(20) NOT NULL,
    -- Teléfono para contacto y recordatorios de devolución
    
    direccion TEXT,
    -- Dirección opcional, útil para envíos o verificación
    
    dni VARCHAR(20) UNIQUE,
    -- Documento de identidad único para validación
    
    fecha_registro TIMESTAMPTZ DEFAULT NOW(),
    -- Timestamp con zona horaria para auditoría
    
    activo BOOLEAN DEFAULT TRUE,
    -- Soft delete: permite desactivar sin eliminar historial
    
    notas TEXT,
    -- Campo libre para observaciones (ej: "cliente frecuente", "requiere depósito")
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
    -- Auditoría de cambios
);

-- Índices para optimizar búsquedas comunes
CREATE INDEX idx_clientes_email ON clientes(email);
CREATE INDEX idx_clientes_telefono ON clientes(telefono);
CREATE INDEX idx_clientes_dni ON clientes(dni);
CREATE INDEX idx_clientes_activo ON clientes(activo);

COMMENT ON TABLE clientes IS 'Registro de clientes del negocio de alquiler de disfraces';
COMMENT ON COLUMN clientes.activo IS 'Permite desactivar clientes sin perder historial de alquileres';



-- TABLA: categorias
-- Categorización de disfraces para mejor organización

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    -- SERIAL para IDs secuenciales simples en catálogo pequeño
    
    nombre VARCHAR(100) NOT NULL UNIQUE,
    -- Ej: "Superhéroes", "Princesas", "Terror", "Profesiones"
    
    descripcion TEXT,
    -- Descripción detallada de la categoría
    
    activo BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categorias_activo ON categorias(activo);

COMMENT ON TABLE categorias IS 'Categorías para clasificar disfraces y facilitar búsquedas';



-- TABLA: disfraces
-- Inventario de disfraces disponibles para alquiler

CREATE TABLE disfraces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    nombre VARCHAR(200) NOT NULL,
    -- Nombre descriptivo del disfraz
    
    descripcion TEXT,
    -- Descripción detallada, útil para IA que procesa imágenes
    
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    -- Relación con categorías, SET NULL si se elimina la categoría
    
    talla VARCHAR(20),
    -- Ej: "XS", "S", "M", "L", "XL", "Única", "6-8 años"
    
    genero VARCHAR(20),
    -- Ej: "Unisex", "Masculino", "Femenino", "Infantil"
    
    stock_total INTEGER NOT NULL DEFAULT 1 CHECK (stock_total >= 0),
    -- Cantidad total de unidades de este disfraz
    -- CHECK asegura que nunca sea negativo
    
    stock_disponible INTEGER NOT NULL DEFAULT 1 CHECK (stock_disponible >= 0),
    -- Cantidad actualmente disponible para alquilar
    -- Este campo se actualiza automáticamente con triggers
    
    costo_compra DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (costo_compra >= 0),
    -- Costo de adquisición del disfraz para control de inversión
    
    estado_conservacion VARCHAR(50) DEFAULT 'Nuevo',
    -- Ej: "Nuevo", "Bueno", "Regular", "Requiere reparación"
    -- CAMBIO: Default modificado de 'Bueno' a 'Nuevo'
    
    imagen_url TEXT,
    -- URL de la imagen del disfraz (almacenada en Supabase Storage)
    
    activo BOOLEAN DEFAULT TRUE,
    -- Permite desactivar disfraces sin eliminarlos
    
    notas TEXT,
    -- Observaciones: "incluye accesorios", "falta botón", etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- CONSTRAINT crítico: stock disponible nunca puede exceder stock total
    CONSTRAINT chk_stock_disponible_valido CHECK (stock_disponible <= stock_total)
);

-- Índices para optimizar consultas
CREATE INDEX idx_disfraces_categoria ON disfraces(categoria_id);
CREATE INDEX idx_disfraces_activo ON disfraces(activo);
CREATE INDEX idx_disfraces_stock_disponible ON disfraces(stock_disponible);
CREATE INDEX idx_disfraces_talla ON disfraces(talla);

COMMENT ON TABLE disfraces IS 'Catálogo de disfraces con control de inventario';
COMMENT ON COLUMN disfraces.stock_total IS 'Inventario total de unidades';
COMMENT ON COLUMN disfraces.stock_disponible IS 'Unidades disponibles para alquilar (actualizado automáticamente)';
COMMENT ON COLUMN disfraces.costo_compra IS 'Costo de adquisición del disfraz para análisis de rentabilidad';
COMMENT ON COLUMN disfraces.estado_conservacion IS 'Estado de conservación del disfraz. Valores: Nuevo, Bueno, Regular, Requiere reparación. Default: Nuevo';



-- TABLA: alquileres
-- Registro de todas las transacciones de alquiler

CREATE TABLE alquileres (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
    -- RESTRICT evita eliminar clientes con alquileres activos
    
    disfraz_id UUID NOT NULL REFERENCES disfraces(id) ON DELETE RESTRICT,
    -- RESTRICT evita eliminar disfraces con alquileres activos
    
    cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    -- Cantidad de unidades del mismo disfraz alquiladas
    
    fecha_salida TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Fecha y hora en que se entrega el disfraz
    
    fecha_retorno_prevista TIMESTAMPTZ NOT NULL,
    -- Fecha acordada de devolución
    
    fecha_retorno_real TIMESTAMPTZ,
    -- Fecha real de devolución (NULL mientras esté alquilado)
    
    estado VARCHAR(50) NOT NULL DEFAULT 'activo',
    -- Estados: 'reservado', 'activo', 'retornado', 'con_demora', 'cancelado'
    
    precio_alquiler_dia DECIMAL(10, 2) NOT NULL CHECK (precio_alquiler_dia >= 0),
    -- Precio por día definido en esta transacción específica
    -- Permite flexibilidad: descuentos, precios especiales, ajustes por temporada
    
    monto_alquiler DECIMAL(10, 2) NOT NULL CHECK (monto_alquiler >= 0),
    -- Monto total cobrado por el alquiler (calculado o ingresado manualmente)
    
    deposito_requerido DECIMAL(10, 2) DEFAULT 0 CHECK (deposito_requerido >= 0),
    -- Monto del depósito requerido para este alquiler específico
    -- CAMBIO: Campo agregado para reemplazar el depósito estático en disfraces
    -- Permite depósitos dinámicos por transacción
    
    deposito_cobrado DECIMAL(10, 2) DEFAULT 0 CHECK (deposito_cobrado >= 0),
    -- Depósito cobrado al cliente para esta transacción específica
    
    deposito_devuelto BOOLEAN DEFAULT FALSE,
    -- Indica si el depósito ya fue devuelto
    
    metodo_pago VARCHAR(50),
    -- Ej: "Efectivo", "Tarjeta", "Transferencia"
    
    notas TEXT,
    -- Observaciones: "cliente llegó tarde", "disfraz con manchas al retornar"
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- CONSTRAINT: fecha de retorno prevista debe ser posterior a fecha de salida
    CONSTRAINT chk_fechas_validas CHECK (fecha_retorno_prevista > fecha_salida),
    
    -- CONSTRAINT: si hay retorno real, debe ser posterior a salida
    CONSTRAINT chk_retorno_real_valido CHECK (
        fecha_retorno_real IS NULL OR fecha_retorno_real >= fecha_salida
    )
);

-- Índices para consultas comunes
CREATE INDEX idx_alquileres_cliente ON alquileres(cliente_id);
CREATE INDEX idx_alquileres_disfraz ON alquileres(disfraz_id);
CREATE INDEX idx_alquileres_estado ON alquileres(estado);
CREATE INDEX idx_alquileres_fecha_salida ON alquileres(fecha_salida);
CREATE INDEX idx_alquileres_fecha_retorno_prevista ON alquileres(fecha_retorno_prevista);

COMMENT ON TABLE alquileres IS 'Registro de transacciones de alquiler de disfraces';
COMMENT ON COLUMN alquileres.estado IS 'Estados válidos: reservado, activo, retornado, con_demora, cancelado';
COMMENT ON COLUMN alquileres.precio_alquiler_dia IS 'Precio por día definido en esta transacción (permite precios dinámicos)';
COMMENT ON COLUMN alquileres.deposito_requerido IS 'Monto del depósito requerido para este alquiler específico. Permite depósitos dinámicos por transacción.';
COMMENT ON COLUMN alquileres.deposito_cobrado IS 'Depósito específico de esta transacción (puede variar según cliente/disfraz)';



-- FUNCIÓN: actualizar_stock_al_alquilar
-- Reduce el stock disponible cuando se crea/activa un alquiler

CREATE OR REPLACE FUNCTION actualizar_stock_al_alquilar()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo procesar si el alquiler está en estado 'activo' o 'reservado'
    IF NEW.estado IN ('activo', 'reservado') THEN
        
        -- Verificar que hay stock suficiente
        IF (SELECT stock_disponible FROM disfraces WHERE id = NEW.disfraz_id) < NEW.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente. No se puede alquilar % unidades del disfraz %', 
                NEW.cantidad, NEW.disfraz_id;
        END IF;
        
        -- Reducir el stock disponible
        UPDATE disfraces
        SET stock_disponible = stock_disponible - NEW.cantidad,
            updated_at = NOW()
        WHERE id = NEW.disfraz_id;
        
        RAISE NOTICE 'Stock reducido en % unidades para disfraz %', NEW.cantidad, NEW.disfraz_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION actualizar_stock_al_alquilar IS 
'Reduce automáticamente el stock disponible al crear un alquiler activo o reservado';



-- FUNCIÓN: actualizar_stock_al_retornar
-- Aumenta el stock disponible cuando se marca un alquiler como retornado

CREATE OR REPLACE FUNCTION actualizar_stock_al_retornar()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el estado cambió de algo diferente a 'retornado' → 'retornado'
    IF OLD.estado != 'retornado' AND NEW.estado = 'retornado' THEN
        
        -- Aumentar el stock disponible
        UPDATE disfraces
        SET stock_disponible = stock_disponible + NEW.cantidad,
            updated_at = NOW()
        WHERE id = NEW.disfraz_id;
        
        -- Registrar fecha de retorno si no está establecida
        IF NEW.fecha_retorno_real IS NULL THEN
            NEW.fecha_retorno_real := NOW();
        END IF;
        
        RAISE NOTICE 'Stock incrementado en % unidades para disfraz %', NEW.cantidad, NEW.disfraz_id;
    END IF;
    
    -- Si se cancela un alquiler que estaba activo/reservado, devolver stock
    IF OLD.estado IN ('activo', 'reservado') AND NEW.estado = 'cancelado' THEN
        UPDATE disfraces
        SET stock_disponible = stock_disponible + NEW.cantidad,
            updated_at = NOW()
        WHERE id = NEW.disfraz_id;
        
        RAISE NOTICE 'Stock recuperado por cancelación: % unidades para disfraz %', 
            NEW.cantidad, NEW.disfraz_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION actualizar_stock_al_retornar IS 
'Aumenta automáticamente el stock disponible al retornar o cancelar un alquiler';



-- FUNCIÓN: validar_stock_antes_actualizar
-- Previene que un UPDATE de alquiler cause stock negativo

CREATE OR REPLACE FUNCTION validar_stock_antes_actualizar()
RETURNS TRIGGER AS $$
DECLARE
    stock_actual INTEGER;
    diferencia INTEGER;
BEGIN
    -- Si cambió la cantidad del alquiler
    IF NEW.cantidad != OLD.cantidad AND NEW.estado IN ('activo', 'reservado') THEN
        
        diferencia := NEW.cantidad - OLD.cantidad;
        
        SELECT stock_disponible INTO stock_actual
        FROM disfraces
        WHERE id = NEW.disfraz_id;
        
        IF stock_actual < diferencia THEN
            RAISE EXCEPTION 'No se puede aumentar el alquiler. Stock insuficiente.';
        END IF;
        
        -- Ajustar stock
        UPDATE disfraces
        SET stock_disponible = stock_disponible - diferencia,
            updated_at = NOW()
        WHERE id = NEW.disfraz_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION validar_stock_antes_actualizar IS 
'Valida y ajusta stock al modificar la cantidad de un alquiler activo';



-- TRIGGERS: Automatización de control de stock


-- Trigger al INSERTAR nuevo alquiler
CREATE TRIGGER trg_alquiler_insert_stock
AFTER INSERT ON alquileres
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock_al_alquilar();

-- Trigger al ACTUALIZAR alquiler (retornos, cancelaciones, cambios de estado)
CREATE TRIGGER trg_alquiler_update_stock
AFTER UPDATE ON alquileres
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock_al_retornar();

-- Trigger para validar cambios en cantidad
CREATE TRIGGER trg_alquiler_update_cantidad
BEFORE UPDATE ON alquileres
FOR EACH ROW
EXECUTE FUNCTION validar_stock_antes_actualizar();



-- FUNCIÓN: actualizar_timestamp
-- Actualiza automáticamente el campo updated_at

CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger de timestamp a todas las tablas
CREATE TRIGGER trg_clientes_updated_at
BEFORE UPDATE ON clientes
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trg_disfraces_updated_at
BEFORE UPDATE ON disfraces
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trg_alquileres_updated_at
BEFORE UPDATE ON alquileres
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();



-- VISTA: alquileres_activos
-- Vista optimizada para consultar alquileres no retornados

CREATE OR REPLACE VIEW alquileres_activos AS
SELECT 
    a.id,
    c.nombre || ' ' || c.apellido AS cliente_nombre,
    c.telefono AS cliente_telefono,
    d.nombre AS disfraz_nombre,
    a.cantidad,
    a.fecha_salida,
    a.fecha_retorno_prevista,
    a.estado,
    a.precio_alquiler_dia,
    a.monto_alquiler,
    a.deposito_requerido,
    a.deposito_cobrado,
    CASE 
        WHEN a.fecha_retorno_prevista < NOW() AND a.estado = 'activo' THEN TRUE
        ELSE FALSE
    END AS tiene_demora,
    EXTRACT(DAY FROM NOW() - a.fecha_retorno_prevista) AS dias_demora
FROM alquileres a
JOIN clientes c ON a.cliente_id = c.id
JOIN disfraces d ON a.disfraz_id = d.id
WHERE a.estado IN ('activo', 'reservado', 'con_demora')
ORDER BY a.fecha_retorno_prevista ASC;

COMMENT ON VIEW alquileres_activos IS 
'Vista de alquileres pendientes con cálculo automático de demoras';



-- VISTA: inventario_disponibilidad
-- Resumen del inventario con disponibilidad actual

CREATE OR REPLACE VIEW inventario_disponibilidad AS
SELECT 
    d.id,
    d.nombre,
    cat.nombre AS categoria,
    d.talla,
    d.stock_total,
    d.stock_disponible,
    d.stock_total - d.stock_disponible AS unidades_alquiladas,
    ROUND(d.costo_compra, 2) AS costo_compra,
    d.estado_conservacion,
    d.activo,
    CASE 
        WHEN d.stock_disponible = 0 THEN 'Sin stock'
        WHEN d.stock_disponible < d.stock_total * 0.3 THEN 'Stock bajo'
        ELSE 'Stock disponible'
    END AS alerta_stock
FROM disfraces d
LEFT JOIN categorias cat ON d.categoria_id = cat.id
WHERE d.activo = TRUE
ORDER BY d.stock_disponible ASC;

COMMENT ON VIEW inventario_disponibilidad IS 
'Vista del inventario con alertas de disponibilidad';



-- VISTA: analisis_rentabilidad
-- Análisis de rentabilidad por disfraz

CREATE OR REPLACE VIEW analisis_rentabilidad AS
SELECT 
    d.id AS disfraz_id,
    d.nombre AS disfraz_nombre,
    cat.nombre AS categoria,
    d.costo_compra,
    d.stock_total,
    COUNT(a.id) AS total_alquileres,
    COALESCE(SUM(a.monto_alquiler), 0) AS ingresos_totales,
    COALESCE(SUM(a.monto_alquiler), 0) - d.costo_compra AS ganancia_neta,
    CASE 
        WHEN d.costo_compra > 0 THEN 
            ROUND((COALESCE(SUM(a.monto_alquiler), 0) / d.costo_compra * 100), 2)
        ELSE 0
    END AS roi_porcentaje,
    CASE
        WHEN COUNT(a.id) > 0 THEN
            ROUND(COALESCE(SUM(a.monto_alquiler), 0) / COUNT(a.id), 2)
        ELSE 0
    END AS ingreso_promedio_por_alquiler
FROM disfraces d
LEFT JOIN categorias cat ON d.categoria_id = cat.id
LEFT JOIN alquileres a ON d.id = a.disfraz_id AND a.estado = 'retornado'
WHERE d.activo = TRUE
GROUP BY d.id, d.nombre, cat.nombre, d.costo_compra, d.stock_total
ORDER BY ganancia_neta DESC;

COMMENT ON VIEW analisis_rentabilidad IS 
'Análisis de rentabilidad e ingresos por disfraz';



-- RESUMEN DE CAMBIOS APLICADOS EN ESTA VERSIÓN

--
-- VERSIÓN 3.0 - CAMBIOS PRINCIPALES:
--
-- 1. DEPÓSITOS DINÁMICOS:
--    - Eliminada columna 'deposito' de tabla 'disfraces'
--    - Agregada columna 'deposito_requerido' en tabla 'alquileres'
--    - Ahora cada alquiler puede tener un depósito diferente
--
-- 2. ESTADO DE CONSERVACIÓN:
--    - Default cambiado de 'Bueno' a 'Nuevo'
--    - Los disfraces nuevos se marcarán automáticamente como "Nuevo"
--
-- 3. VISTAS ACTUALIZADAS:
--    - Vista 'alquileres_activos' ahora incluye 'deposito_requerido'
--
