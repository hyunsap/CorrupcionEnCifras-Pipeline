import psycopg2
import csv
import os
import re
from datetime import datetime

os.chdir('/app/data')

# ============================================
# Configuración de conexión
# ============================================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "corrupcion_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "td8corrupcion"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
}

def conectar_db():
    return psycopg2.connect(**DB_CONFIG)

def parse_nullable(value):
    """Convierte strings vacíos en None"""
    if value is None or str(value).strip() == "":
        return None
    return value

def parse_nullable_date(value):
    """Convierte cadenas de fecha a formato ISO, manejando múltiples formatos"""
    if not value or str(value).strip() == "":
        return None
    
    value = str(value).strip()
    
    # Lista de formatos de fecha a probar
    formatos = [
        "%Y-%m-%d",      # 2023-12-31
        "%d/%m/%Y",      # 31/12/2023
        "%d-%m-%Y",      # 31-12-2023
        "%d-%m-%y",      # 31-12-23
        "%y-%m-%d",      # 23-12-31
    ]
    
    for formato in formatos:
        try:
            fecha = datetime.strptime(value, formato)
            return fecha.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Si no coincide con ningún formato, intentar parsear manualmente
    # Para casos como "15-05-13" que podría ser año-mes-día con año corto
    if re.match(r'^\d{2}-\d{2}-\d{2}$', value):
        partes = value.split('-')
        try:
            year = int(partes[0])
            month = int(partes[1])
            day = int(partes[2])
            
            # Convertir año de 2 dígitos a 4
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            fecha = datetime(year, month, day)
            return fecha.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass
    
    print(f"⚠️ Advertencia: formato de fecha no reconocido: {value}")
    return None

def parsear_delito(delito_str):
    """
    Parsea un string de delito y extrae: nombre, artículo, ley
    
    Ejemplos:
    "Art. 210 CP - ASOCIACION ILICITA" 
    -> nombre: "ASOCIACION ILICITA", articulo: "210", ley: "CP"
    
    "ASOCIACION ILICITA"
    -> nombre: "ASOCIACION ILICITA", articulo: None, ley: None
    """
    delito_str = delito_str.strip()
    
    # Patrón 1: "Art. 210 CP - NOMBRE" o "Art 210 - NOMBRE"
    patron1 = r'(?:Art\.?\s*)?(\d+(?:\s*(?:inc|bis|ter)\.?\s*\d+)?)\s*([A-Z\.]+)?\s*-\s*(.+)'
    
    # Patrón 2: "NOMBRE (Art. 210 CP)"
    patron2 = r'(.+?)\s*\((?:Art\.?\s*)?(\d+(?:\s*(?:inc|bis|ter)\.?\s*\d+)?)\s*([A-Z\.]+)?\)'
    
    # Patrón 3: Solo artículo al inicio sin "Art."
    patron3 = r'^(\d+)\s+([A-Z\.]+)?\s*-?\s*(.+)'
    
    match = re.match(patron1, delito_str)
    if match:
        articulo = match.group(1).strip() if match.group(1) else None
        ley = match.group(2).strip() if match.group(2) else None
        nombre = match.group(3).strip() if match.group(3) else delito_str
        return nombre, articulo, ley
    
    match = re.match(patron2, delito_str)
    if match:
        nombre = match.group(1).strip()
        articulo = match.group(2).strip() if match.group(2) else None
        ley = match.group(3).strip() if match.group(3) else None
        return nombre, articulo, ley
    
    match = re.match(patron3, delito_str)
    if match and len(match.group(1)) <= 4:  # Evitar falsos positivos
        articulo = match.group(1).strip()
        ley = match.group(2).strip() if match.group(2) else None
        nombre = match.group(3).strip() if match.group(3) else delito_str
        return nombre, articulo, ley
    
    # Si no matchea ningún patrón, devolver solo el nombre
    return delito_str, None, None

# ============================================
# Funciones de limpieza previas
# ============================================

def limpiar_tablas(conn):
    """Limpia las tablas en el orden correcto para evitar violaciones de FK"""
    print("Limpiando tablas existentes...")
    try:
        with conn.cursor() as cur:
            # Orden: primero las tablas dependientes, luego las principales
            tablas = [
                "tribunal_juez",
                "representacion",
                "expediente_delito",
                "rol_parte",
                "parte",
                "plazo",
                "resolucion",
                "radicacion",
                "expediente",
                "juez",
                "secretaria",
                "tribunal",
                "jurisdiccion",
                "fuero",
                "letrado",
                "tipo_delito" 
            ]
            
            for tabla in tablas:
                cur.execute(f"DELETE FROM {tabla}")
                print(f"  ✓ {tabla} limpiada")
            
            # Reiniciar secuencias
            secuencias = [
                "fuero_fuero_id_seq",
                "jurisdiccion_jurisdiccion_id_seq",
                "tribunal_tribunal_id_seq",
                "juez_juez_id_seq",
                "letrado_letrado_id_seq",
                "parte_parte_id_seq",
                "resolucion_id_resolucion_seq",
                "radicacion_radicacion_id_seq",
                "tipo_delito_tipo_delito_id_seq" 
            ]
            
            for seq in secuencias:
                try:
                    cur.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
                except Exception as e:
                    print(f"No se pudo reiniciar {seq}: {e}")
        
        conn.commit()
        print("Limpieza completada\n")
    except Exception as e:
        conn.rollback()
        print(f"Error en limpieza: {e}")

# ============================================
# Funciones de carga
# ============================================

def cargar_fuero(conn):
    print("Cargando fueros...")
    count = 0
    try:
        with conn.cursor() as cur, open("etl_fueros.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO fuero (fuero_id, nombre)
                    VALUES (%s, %s)
                    ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
                """, (parse_nullable(row["fuero_id"]), parse_nullable(row["nombre"])))
                count += 1
        conn.commit()
        print(f"Fueros insertados: {count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar fueros: {e}")

def cargar_jurisdiccion(conn):
    print("Cargando jurisdicciones...")
    count = 0
    try:
        with conn.cursor() as cur, open("etl_jurisdicciones.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO jurisdiccion (jurisdiccion_id, ambito, departamento_judicial)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (jurisdiccion_id) DO UPDATE 
                    SET ambito = EXCLUDED.ambito,
                        departamento_judicial = EXCLUDED.departamento_judicial
                """, (
                    parse_nullable(row["jurisdiccion_id"]),
                    parse_nullable(row["ambito"]),
                    parse_nullable(row["departamento_judicial"])
                ))
                count += 1
        conn.commit()
        print(f"Jurisdicciones insertadas: {count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar jurisdicciones: {e}")

def cargar_tribunal(conn):
    print("Cargando tribunales...")
    count = 0
    try:
        with conn.cursor() as cur, open("etl_tribunales.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO tribunal (
                        tribunal_id, nombre, domicilio_sede,
                        contacto, jurisdiccion_id, fuero
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (nombre) DO UPDATE 
                    SET domicilio_sede = EXCLUDED.domicilio_sede,
                        contacto = EXCLUDED.contacto,
                        jurisdiccion_id = EXCLUDED.jurisdiccion_id,
                        fuero = EXCLUDED.fuero
                """, (
                    parse_nullable(row["tribunal_id"]),
                    parse_nullable(row["nombre"]),
                    parse_nullable(row["domicilio_sede"]),
                    parse_nullable(row["contacto"]),
                    parse_nullable(row["jurisdiccion_id"]),
                    parse_nullable(row["fuero"])
                ))
                count += 1
        conn.commit()
        print(f"Tribunales insertados: {count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar tribunales: {e}")

def cargar_expediente(conn):
    print("Cargando expedientes...")
    count = 0
    errores = 0
    try:
        with conn.cursor() as cur, open("etl_expedientes.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cur.execute("""
                        INSERT INTO expediente (
                            numero_expediente, caratula, jurisdiccion, tribunal,
                            estado_procesal, fecha_inicio, fecha_ultimo_movimiento,
                            camara_origen, ano_inicio, delitos, fiscal, fiscalia
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (numero_expediente) DO UPDATE 
                        SET caratula = EXCLUDED.caratula,
                            estado_procesal = EXCLUDED.estado_procesal,
                            fecha_ultimo_movimiento = EXCLUDED.fecha_ultimo_movimiento
                    """, (
                        parse_nullable(row["numero_expediente"]),
                        parse_nullable(row["caratula"]),
                        parse_nullable(row["jurisdiccion"]),
                        parse_nullable(row["tribunal"]),
                        parse_nullable(row["estado_procesal"]),
                        parse_nullable_date(row["fecha_inicio"]),
                        parse_nullable_date(row["fecha_ultimo_movimiento"]),
                        parse_nullable(row["camara_origen"]),
                        parse_nullable(row["ano_inicio"]),
                        parse_nullable(row["delitos"]),
                        parse_nullable(row["fiscal"]),
                        parse_nullable(row["fiscalia"])
                    ))
                    count += 1
                except Exception as e:
                    errores += 1
                    if errores <= 5:  # Mostrar solo los primeros 5 errores
                        print(f"Error en expediente {row.get('numero_expediente')}: {e}")
        conn.commit()
        print(f"Expedientes insertados: {count} (errores: {errores})")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar expedientes: {e}")

def cargar_parte_y_rol(conn):
    print("Cargando partes y roles...")
    parte_count = rol_count = 0
    try:
        with conn.cursor() as cur, open("etl_partes.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO parte (numero_expediente, nombre_razon_social)
                    VALUES (%s, %s)
                    RETURNING parte_id
                """, (parse_nullable(row["numero_expediente"]), parse_nullable(row["nombre"])))
                parte_id = None
                try:
                    parte_id = cur.fetchone()[0]
                except:
                    pass
                parte_count += 1

                if parte_id and row.get("rol"):
                    cur.execute("""
                        INSERT INTO rol_parte (parte_id, nombre)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (parte_id, parse_nullable(row["rol"])))
                    rol_count += 1
        conn.commit()
        print(f"Partes insertadas: {parte_count}, Roles insertados: {rol_count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar partes/roles: {e}")

def cargar_letrado(conn):
    print("Cargando letrados...")
    count = 0
    try:
        with conn.cursor() as cur, open("etl_letrados.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = parse_nullable(row.get("letrado"))
                if not nombre:
                    continue
                cur.execute("""
                    INSERT INTO letrado (nombre)
                    VALUES (%s)
                    ON CONFLICT (nombre) DO NOTHING
                """, (nombre,))
                count += 1
        conn.commit()
        print(f"Letrados insertados: {count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar letrados: {e}")

def cargar_representacion(conn):
    print("Cargando representaciones...")
    count = 0
    errores = 0
    try:
        with conn.cursor() as cur, open("etl_representaciones.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cur.execute("SELECT parte_id FROM parte WHERE nombre_razon_social = %s AND numero_expediente = %s",
                                (parse_nullable(row["nombre_parte"]), parse_nullable(row["numero_expediente"])))
                    parte_id = cur.fetchone()

                    cur.execute("SELECT letrado_id FROM letrado WHERE nombre = %s",
                                (parse_nullable(row["letrado"]),))
                    letrado_id = cur.fetchone()

                    if parte_id and letrado_id:
                        cur.execute("""
                            INSERT INTO representacion (numero_expediente, parte_id, letrado_id, rol)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (
                            parse_nullable(row["numero_expediente"]),
                            parte_id[0],
                            letrado_id[0],
                            parse_nullable(row.get("rol"))
                        ))
                        count += 1
                    else:
                        errores += 1
                except Exception as e:
                    errores += 1
                    if errores <= 3:
                        print(f"Error en representación: {e}")
        conn.commit()
        print(f"Representaciones insertadas: {count} (no encontrados: {errores})")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar representaciones: {e}")

def cargar_resolucion(conn):
    print("Cargando resoluciones...")
    count = 0
    errores = 0
    try:
        with conn.cursor() as cur, open("etl_resoluciones.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    fecha = parse_nullable_date(row["fecha"])
                    cur.execute("""
                        INSERT INTO resolucion (numero_expediente, fecha, nombre, link)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        parse_nullable(row["numero_expediente"]),
                        fecha,
                        parse_nullable(row["nombre"]),
                        parse_nullable(row["link"])
                    ))
                    count += 1
                except Exception as e:
                    errores += 1
                    if errores <= 5:
                        print(f"Error en resolución {row.get('numero_expediente')}, fecha '{row.get('fecha')}': {e}")
        conn.commit()
        print(f"Resoluciones insertadas: {count} (errores: {errores})")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar resoluciones: {e}")

def cargar_radicacion(conn):
    print("Cargando radicaciones...")
    count = 0
    errores = 0
    try:
        with conn.cursor() as cur, open("etl_radicaciones.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cur.execute("""
                        INSERT INTO radicacion (
                            numero_expediente, orden, fecha_radicacion,
                            tribunal, fiscal_nombre, fiscalia
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (numero_expediente, orden) DO UPDATE
                        SET fecha_radicacion = EXCLUDED.fecha_radicacion,
                            tribunal = EXCLUDED.tribunal,
                            fiscal_nombre = EXCLUDED.fiscal_nombre,
                            fiscalia = EXCLUDED.fiscalia
                    """, (
                        parse_nullable(row["numero_expediente"]),
                        parse_nullable(row["orden"]),
                        parse_nullable_date(row["fecha_radicacion"]),
                        parse_nullable(row["tribunal"]),
                        parse_nullable(row["fiscal_nombre"]),
                        parse_nullable(row["fiscalia"])
                    ))
                    count += 1
                except Exception as e:
                    errores += 1
                    if errores <= 3:
                        print(f"Error en radicación: {e}")
        conn.commit()
        print(f"Radicaciones insertadas: {count} (errores: {errores})")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar radicaciones: {e}")

def cargar_juez(conn):
    print("Cargando jueces...")
    count = 0
    try:
        with conn.cursor() as cur, open("etl_jueces.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO juez (juez_id, nombre, email, telefono)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (nombre) DO UPDATE 
                    SET email = EXCLUDED.email,
                        telefono = EXCLUDED.telefono
                """, (
                    parse_nullable(row["juez_id"]),
                    parse_nullable(row["nombre"]),
                    parse_nullable(row["email"]),
                    parse_nullable(row["telefono"])
                ))
                count += 1
        conn.commit()
        print(f"Jueces insertados: {count}")
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar jueces: {e}")

def cargar_tribunal_juez(conn):
    print("Cargando relaciones tribunal-juez...")
    count = 0
    errores = 0
    try:
        with open("etl_tribunal_juez.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    with conn.cursor() as cur:  
                        
                        cur.execute("SELECT tribunal_id FROM tribunal WHERE tribunal_id = %s", 
                                   (parse_nullable(row["tribunal_id"]),))
                        if not cur.fetchone():
                            errores += 1
                            continue
                        
                        cur.execute("SELECT juez_id FROM juez WHERE juez_id = %s", 
                                   (parse_nullable(row["juez_id"]),))
                        if not cur.fetchone():
                            errores += 1
                            continue
                        
                        cur.execute("""
                            INSERT INTO tribunal_juez (tribunal_id, juez_id, cargo, situacion)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (tribunal_id, juez_id) DO UPDATE
                            SET cargo = EXCLUDED.cargo,
                                situacion = EXCLUDED.situacion
                        """, (
                            parse_nullable(row["tribunal_id"]),
                            parse_nullable(row["juez_id"]),
                            parse_nullable(row["cargo"]),
                            parse_nullable(row["situacion"])
                        ))
                        conn.commit()  # Commit después de cada INSERT exitoso
                        count += 1
                except Exception as e:
                    conn.rollback()  # Rollback solo de esta fila
                    errores += 1
                    if errores <= 3:
                        print(f" Error en tribunal-juez: {e}")
        
        print(f"Relaciones tribunal-juez insertadas: {count} (errores: {errores})")
    except Exception as e:
        print(f"Error al cargar tribunal-juez: {e}")

def extraer_y_cargar_delitos(conn):
    """Extrae delitos únicos de expedientes y los normaliza en tipo_delito"""
    print("Extrayendo y cargando tipos de delito...")
    count = 0
    errores = 0
    
    try:
        with conn.cursor() as cur:
            # Obtener todos los delitos únicos de la columna delitos
            cur.execute("""
                SELECT DISTINCT TRIM(unnest(string_to_array(delitos, ','))) as delito
                FROM expediente 
                WHERE delitos IS NOT NULL AND delitos != ''
            """)
            
            delitos_raw = cur.fetchall()
            delitos_procesados = set()  # Para evitar duplicados por nombre
            
            for (delito_raw,) in delitos_raw:
                if not delito_raw or not delito_raw.strip():
                    continue
                
                try:
                    nombre, articulo, ley = parsear_delito(delito_raw)
                    
                    # Usar nombre como clave única
                    if nombre not in delitos_procesados:
                        cur.execute("""
                            INSERT INTO tipo_delito (nombre, articulo, ley)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (nombre) DO UPDATE
                            SET articulo = COALESCE(EXCLUDED.articulo, tipo_delito.articulo),
                                ley = COALESCE(EXCLUDED.ley, tipo_delito.ley)
                        """, (nombre, articulo, ley))
                        delitos_procesados.add(nombre)
                        count += 1
                except Exception as e:
                    errores += 1
                    if errores <= 5:
                        print(f"Error parseando delito '{delito_raw}': {e}")
            
            conn.commit()
            print(f"Tipos de delito insertados: {count} (errores: {errores})")
                    
    except Exception as e:
        conn.rollback()
        print(f"Error al cargar tipos de delito: {e}")

def vincular_expedientes_delitos(conn):
    """Vincula expedientes con sus delitos normalizados en expediente_delito"""
    print("Vinculando expedientes con delitos...")
    count = 0
    errores = 0
    no_encontrados = 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT numero_expediente, delitos 
                FROM expediente 
                WHERE delitos IS NOT NULL AND delitos != ''
            """)
            
            expedientes = cur.fetchall()
            
            for numero_exp, delitos_str in expedientes:
                # Separar delitos por coma
                delitos_lista = [d.strip() for d in delitos_str.split(',') if d.strip()]
                
                for delito_raw in delitos_lista:
                    try:
                        nombre, _, _ = parsear_delito(delito_raw)
                        
                        # Buscar el tipo_delito_id por nombre
                        cur.execute("""
                            SELECT tipo_delito_id FROM tipo_delito WHERE nombre = %s
                        """, (nombre,))
                        
                        result = cur.fetchone()
                        if result:
                            tipo_delito_id = result[0]
                            cur.execute("""
                                INSERT INTO expediente_delito (numero_expediente, tipo_delito_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """, (numero_exp, tipo_delito_id))
                            count += 1
                        else:
                            no_encontrados += 1
                            if no_encontrados <= 3:
                                print(f"Delito no encontrado: '{nombre}' en exp {numero_exp}")
                    except Exception as e:
                        errores += 1
                        if errores <= 5:
                            print(f"Error vinculando {numero_exp}: {e}")
            
            conn.commit()
            print(f"Vínculos expediente-delito creados: {count} (errores: {errores}, no encontrados: {no_encontrados})")
            
    except Exception as e:
        conn.rollback()
        print(f"Error al vincular expedientes con delitos: {e}")

# Funciones de metadata para agregar aviso de última actualización de datos
def crear_tabla_metadata_si_no_existe(conn):
    """Crea la tabla metadata si no existe"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    clave VARCHAR(50) PRIMARY KEY,
                    valor TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()
        print("Tabla metadata actualizada/creada")
    except Exception as e:
        print(f"Advertencia al crear tabla metadata: {e}")

def actualizar_metadata_ultima_actualizacion(conn):
    """
    Actualiza la fecha de última actualización en la tabla metadata.
    Esta función debe llamarse al final del proceso de carga exitoso.
    
    Args:
        conn: Conexión a la base de datos (psycopg2)
    """
    try:
        with conn.cursor() as cur:
            # Insertar o actualizar la fecha de última actualización
            cur.execute("""
                INSERT INTO metadata (clave, valor)
                VALUES ('ultima_actualizacion', NOW())
                ON CONFLICT (clave) 
                DO UPDATE SET valor = NOW()
            """)
        conn.commit()
        print("Fecha de última actualización actualizada en metadata")
    except Exception as e:
        conn.rollback()
        print(f"Advertencia: No se pudo actualizar metadata: {e}")
        # No lanzamos excepción para no interrumpir el proceso si falla esto

# ============================================
# Main
# ============================================

def main():
    print("=== Iniciando carga mejorada a base de datos ===\n")
    conn = conectar_db()
    carga_exitosa = False  # Flag para saber si todo fue exitoso
    
    try:
        # Crear tabla metadata si no existe
        crear_tabla_metadata_si_no_existe(conn)
        
        # Limpiar tablas antes de cargar
        limpiar_tablas(conn)
        
        # Cargar datos en orden
        cargar_fuero(conn)
        cargar_jurisdiccion(conn)
        cargar_tribunal(conn)
        cargar_expediente(conn)
        cargar_parte_y_rol(conn)
        cargar_letrado(conn)
        cargar_representacion(conn)
        cargar_resolucion(conn)
        cargar_radicacion(conn)
        cargar_juez(conn)
        cargar_tribunal_juez(conn)
        extraer_y_cargar_delitos(conn)
        vincular_expedientes_delitos(conn)
        
        # Si llegamos aquí, todo fue exitoso
        carga_exitosa = True
        
        if carga_exitosa:
            actualizar_metadata_ultima_actualizacion(conn)
        
        print("\n=== Carga completa exitosa ===")
        
    except Exception as e:
        print(f"\n=== Error general: {e} ===")
        print(" La fecha de última actualización NO se actualizó debido a errores")
    finally:
        conn.close()

if __name__ == "_main_":
    main()