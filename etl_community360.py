"""
Script ETL: Community 360 - Fase 2 (Limpieza, Procesamiento y Carga en PostgreSQL / Aiven)
Soporta ejecución completa (Etapas 1 a 8), exportación de CSVs y carga transaccional.
"""

import os
import re
import sys
import argparse
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

def limpiar_texto(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "n/a", "na", "<na>"}:
        return None
    return s

def parse_bool(val):
    if val is None or pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(int(val))
    s = str(val).strip().lower()
    if s in {"1", "true", "si", "sí", "yes", "y", "s", "t"}:
        return True
    return False

def normalizar_etiqueta(tag):
    if not tag or pd.isna(tag):
        return None
    t = str(tag).strip().lower()
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^a-záéíóúüñ0-9_]", "", t)
    return t[:40] if t else None

def parse_fecha(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return pd.to_datetime(val_str, format=fmt).date()
        except Exception:
            pass
    try:
        return pd.to_datetime(val_str, errors="coerce").date()
    except Exception:
        return None

def ejecutar_etl(usuarios_csv="comunidad_virtual_usuarios.csv", 
                 interacciones_csv="comunidad_virtual_1000_interacciones.csv", 
                 out_dir="salida_depurada"):
    os.makedirs(out_dir, exist_ok=True)
    print("=" * 65)
    print("      PROCESO ETL: COMMUNITY 360 - FASE 2 (POSTGRESQL)")
    print("=" * 65)

    # Lectura de datos crudos
    df_u_raw = pd.read_csv(usuarios_csv)
    df_i_raw = pd.read_csv(interacciones_csv)
    total_u_raw = len(df_u_raw)
    total_i_raw = len(df_i_raw)
    print(f"\n[Lectura] Usuarios crudos: {total_u_raw} registros")
    print(f"[Lectura] Interacciones crudas: {total_i_raw} registros")

    # =========================================================================
    # ETAPA 1: Eliminación de registros duplicados
    # =========================================================================
    df_u = df_u_raw.drop_duplicates().copy()
    dup_u_id = df_u.duplicated(subset=["id_usuario"], keep="first").sum()
    df_u = df_u.drop_duplicates(subset=["id_usuario"], keep="first").copy()
    
    dup_u_alias = df_u.duplicated(subset=["alias"], keep="first").sum()
    df_u = df_u.drop_duplicates(subset=["alias"], keep="first").copy()

    df_i = df_i_raw.drop_duplicates().copy()
    dup_i_id = df_i.duplicated(subset=["id_interaccion"], keep="first").sum()
    df_i = df_i.drop_duplicates(subset=["id_interaccion"], keep="first").copy()

    print(f"[Etapa 1] Duplicados eliminados en usuarios: {dup_u_id} por ID, {dup_u_alias} por Alias")
    print(f"[Etapa 1] Duplicados eliminados en interacciones: {dup_i_id} por ID")

    # =========================================================================
    # ETAPA 2: Normalización de valores vacíos y nulos
    # =========================================================================
    for col in df_u.columns:
        if df_u[col].dtype == object:
            df_u[col] = df_u[col].apply(limpiar_texto)
    for col in df_i.columns:
        if df_i[col].dtype == object:
            df_i[col] = df_i[col].apply(limpiar_texto)

    # Filtrar registros sin ID principal
    df_u = df_u[df_u["id_usuario"].notna()].copy()
    df_i = df_i[df_i["id_interaccion"].notna()].copy()

    print(f"[Etapa 2] Normalización de nulos completada. Usuarios: {len(df_u)}, Interacciones: {len(df_i)}")

    # =========================================================================
    # ETAPA 3: Estandarización de fechas, categorías y campos multivaluados
    # =========================================================================
    df_u["fecha_ingreso"] = df_u["fecha_ingreso"].apply(parse_fecha)
    df_u["ultima_actividad"] = df_u["ultima_actividad"].apply(parse_fecha)

    fecha_defecto = pd.to_datetime("2024-01-01").date()
    df_u["fecha_ingreso"] = df_u["fecha_ingreso"].fillna(fecha_defecto)
    df_u["ultima_actividad"] = df_u["ultima_actividad"].fillna(df_u["fecha_ingreso"])

    for cat_col in ["estatus", "interes_principal", "plataforma_principal", "especie_fursona", "rango_edad", "zona_horaria"]:
        if cat_col in df_u.columns:
            df_u[cat_col] = df_u[cat_col].apply(lambda x: str(x).strip().lower() if x else "no_especificado")

    df_u["es_artista"] = df_u["es_artista"].apply(parse_bool)
    df_u["consentimiento_datos"] = df_u["consentimiento_datos"].apply(parse_bool)

    df_i["timestamp_dt"] = pd.to_datetime(df_i["timestamp"], errors="coerce")
    ts_defecto = pd.to_datetime("2024-01-01 00:00:00")
    df_i["timestamp_dt"] = df_i["timestamp_dt"].fillna(ts_defecto)

    for cat_col in ["canal", "tipo", "tema", "idioma", "dispositivo"]:
        if cat_col in df_i.columns:
            df_i[cat_col] = df_i[cat_col].apply(lambda x: str(x).strip().lower() if x else "general")

    etiquetas_set = set()
    interaccion_etiqueta_pairs = []

    for _, row in df_i.iterrows():
        id_int = row["id_interaccion"]
        raw_tags = row.get("etiquetas")
        if raw_tags and isinstance(raw_tags, str):
            for part in raw_tags.split("|"):
                cleaned = normalizar_etiqueta(part)
                if cleaned:
                    etiquetas_set.add(cleaned)
                    interaccion_etiqueta_pairs.append((id_int, cleaned))

    sorted_etiquetas = sorted(list(etiquetas_set))
    etiqueta_to_id = {tag: idx + 1 for idx, tag in enumerate(sorted_etiquetas)}

    df_etiquetas = pd.DataFrame([
        {"id_etiqueta": etiqueta_to_id[tag], "nombre": tag}
        for tag in sorted_etiquetas
    ])

    print(f"[Etapa 3] Categorías y fechas estandarizadas. Etiquetas únicas: {len(df_etiquetas)}")

    # =========================================================================
    # ETAPA 4: Validación estricta de tipos de datos y rangos numéricos
    # =========================================================================
    int_cols_u = ["mensajes_30d", "reacciones_30d", "eventos_asistidos", "comisiones_compradas"]
    for c in int_cols_u:
        df_u[c] = pd.to_numeric(df_u[c], errors="coerce").fillna(0).astype(int).clip(lower=0)

    df_u["sentimiento_promedio"] = pd.to_numeric(df_u["sentimiento_promedio"], errors="coerce").fillna(0.0).astype(float).clip(lower=-1.0, upper=1.0).round(3)

    df_u["latitud"] = pd.to_numeric(df_u["latitud"], errors="coerce").clip(lower=-90.0, upper=90.0)
    df_u["longitud"] = pd.to_numeric(df_u["longitud"], errors="coerce").clip(lower=-180.0, upper=180.0)

    df_i["sentimiento"] = pd.to_numeric(df_i["sentimiento"], errors="coerce").fillna(0.0).astype(float).clip(lower=-1.0, upper=1.0).round(2)
    df_i["reacciones_recibidas"] = pd.to_numeric(df_i["reacciones_recibidas"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    df_i["texto"] = df_i["texto"].fillna("")
    df_i["longitud_texto"] = df_i["texto"].apply(lambda s: len(str(s)))

    print("[Etapa 4] Tipos de datos y rangos numéricos validados.")

    # =========================================================================
    # ETAPA 5: Enriquecimiento y aislamiento de registros anómalos (Huérfanos)
    # =========================================================================
    usuarios_validos_set = set(df_u["id_usuario"].unique())

    mask_valida = df_i["id_usuario"].isin(usuarios_validos_set)
    df_interacciones_validas = df_i[mask_valida].copy()
    df_interacciones_huerfanas = df_i[~mask_valida].copy()

    df_no_vinculadas = pd.DataFrame({
        "id_interaccion": df_interacciones_huerfanas["id_interaccion"],
        "id_usuario_origen": df_interacciones_huerfanas["id_usuario"],
        "timestamp": df_interacciones_huerfanas["timestamp_dt"],
        "canal": df_interacciones_huerfanas["canal"],
        "tipo": df_interacciones_huerfanas["tipo"],
        "texto": df_interacciones_huerfanas["texto"],
        "tema": df_interacciones_huerfanas["tema"],
        "sentimiento": df_interacciones_huerfanas["sentimiento"],
        "idioma": df_interacciones_huerfanas["idioma"],
        "dispositivo": df_interacciones_huerfanas["dispositivo"],
        "longitud_texto": df_interacciones_huerfanas["longitud_texto"],
        "reacciones_recibidas": df_interacciones_huerfanas["reacciones_recibidas"],
        "etiquetas_raw": df_interacciones_huerfanas["etiquetas"].fillna(""),
        "motivo_aislamiento": "usuario_inexistente_en_maestro"
    })

    interacciones_validas_set = set(df_interacciones_validas["id_interaccion"].unique())
    interaccion_etiquetas_validas = [
        {"id_interaccion": pair[0], "id_etiqueta": etiqueta_to_id[pair[1]]}
        for pair in interaccion_etiqueta_pairs
        if pair[0] in interacciones_validas_set and pair[1] in etiqueta_to_id
    ]
    df_interaccion_etiquetas = pd.DataFrame(interaccion_etiquetas_validas).drop_duplicates()

    df_interacciones_final = pd.DataFrame({
        "id_interaccion": df_interacciones_validas["id_interaccion"],
        "id_usuario": df_interacciones_validas["id_usuario"],
        "timestamp": df_interacciones_validas["timestamp_dt"],
        "canal": df_interacciones_validas["canal"],
        "tipo": df_interacciones_validas["tipo"],
        "texto": df_interacciones_validas["texto"],
        "tema": df_interacciones_validas["tema"],
        "sentimiento": df_interacciones_validas["sentimiento"],
        "idioma": df_interacciones_validas["idioma"],
        "dispositivo": df_interacciones_validas["dispositivo"],
        "longitud_texto": df_interacciones_validas["longitud_texto"],
        "reacciones_recibidas": df_interacciones_validas["reacciones_recibidas"]
    })

    print(f"[Etapa 5] Interacciones válidas vinculadas: {len(df_interacciones_final)}")
    print(f"[Etapa 5] Interacciones huérfanas aisladas: {len(df_no_vinculadas)}")

    # =========================================================================
    # ETAPA 6: Tratamiento de privacidad de datos (Privacy by Design)
    # =========================================================================
    cols_usuarios_final = [
        "id_usuario", "alias", "fecha_ingreso", "zona_horaria", "rango_edad",
        "especie_fursona", "interes_principal", "plataforma_principal",
        "es_artista", "mensajes_30d", "reacciones_30d", "eventos_asistidos",
        "comisiones_compradas", "sentimiento_promedio", "ultima_actividad",
        "estatus", "consentimiento_datos"
    ]
    df_usuarios_final = df_u[cols_usuarios_final].copy()

    df_u_con_consentimiento = df_u[df_u["consentimiento_datos"] == True].copy()
    df_ubicaciones_final = pd.DataFrame({
        "id_usuario": df_u_con_consentimiento["id_usuario"],
        "pais": df_u_con_consentimiento["pais"].fillna("no_especificado"),
        "estado": df_u_con_consentimiento["estado"].fillna("no_especificado"),
        "ciudad": df_u_con_consentimiento["ciudad"].fillna("no_especificado"),
        "latitud": df_u_con_consentimiento["latitud"],
        "longitud": df_u_con_consentimiento["longitud"]
    })

    usuarios_sin_consentimiento = len(df_u[df_u["consentimiento_datos"] == False])
    print(f"[Etapa 6] Usuarios con consentimiento (con ubicación cargada): {len(df_ubicaciones_final)}")
    print(f"[Etapa 6] Usuarios sin consentimiento protegidos (ubicación excluida): {usuarios_sin_consentimiento}")

    # =========================================================================
    # ETAPA 7: Exportación de archivos limpios para auditoría
    # =========================================================================
    path_u = os.path.join(out_dir, "usuarios_limpios.csv")
    path_ub = os.path.join(out_dir, "ubicaciones_limpias.csv")
    path_i = os.path.join(out_dir, "interacciones_limpias.csv")
    path_in = os.path.join(out_dir, "interacciones_no_vinculadas.csv")
    path_e = os.path.join(out_dir, "etiquetas_limpias.csv")
    path_ie = os.path.join(out_dir, "interaccion_etiquetas_limpias.csv")

    df_usuarios_final.to_csv(path_u, index=False)
    df_ubicaciones_final.to_csv(path_ub, index=False)
    df_interacciones_final.to_csv(path_i, index=False)
    df_no_vinculadas.to_csv(path_in, index=False)
    df_etiquetas.to_csv(path_e, index=False)
    df_interaccion_etiquetas.to_csv(path_ie, index=False)

    print(f"\n[Etapa 7] CSVs exportados en '{out_dir}/':")
    print(f"  - usuarios_limpios.csv: {len(df_usuarios_final)} registros")
    print(f"  - ubicaciones_limpias.csv: {len(df_ubicaciones_final)} registros")
    print(f"  - interacciones_limpias.csv: {len(df_interacciones_final)} registros")
    print(f"  - interacciones_no_vinculadas.csv: {len(df_no_vinculadas)} registros")
    print(f"  - etiquetas_limpias.csv: {len(df_etiquetas)} registros")
    print(f"  - interaccion_etiquetas_limpias.csv: {len(df_interaccion_etiquetas)} registros")

    data_dict = {
        "usuarios": df_usuarios_final,
        "ubicaciones_usuario": df_ubicaciones_final,
        "interacciones": df_interacciones_final,
        "interacciones_no_vinculadas": df_no_vinculadas,
        "etiquetas": df_etiquetas,
        "interaccion_etiquetas": df_interaccion_etiquetas
    }
    return data_dict

# =============================================================================
# ETAPA 8: Carga Transaccional en PostgreSQL (Aiven)
# =============================================================================
def get_db_engine(db_uri=None):
    if db_uri:
        if db_uri.startswith("postgres://"):
            db_uri = db_uri.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_uri.startswith("postgresql://"):
            db_uri = db_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        return create_engine(db_uri)

    user = os.getenv("AIVEN_DB_USER", "avnadmin")
    password = os.getenv("AIVEN_DB_PASS", "")
    host = os.getenv("AIVEN_DB_HOST", "pg-17441907-tareautm46-43ae.k.aivencloud.com")
    port = os.getenv("AIVEN_DB_PORT", "17635")
    db_name = os.getenv("AIVEN_DB_NAME", "defaultdb")

    if not password:
        raise ValueError("Se requiere contraseña de Aiven o URI completo.")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"
    return create_engine(url)

def crear_tablas_postgres(engine, reiniciar=True):
    drop_statements = [
        "DROP TABLE IF EXISTS interaccion_etiquetas CASCADE;",
        "DROP TABLE IF EXISTS etiquetas CASCADE;",
        "DROP TABLE IF EXISTS interacciones_no_vinculadas CASCADE;",
        "DROP TABLE IF EXISTS interacciones CASCADE;",
        "DROP TABLE IF EXISTS ubicaciones_usuario CASCADE;",
        "DROP TABLE IF EXISTS usuarios CASCADE;"
    ]
    ddl_statements = [
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
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
        """,
        """
        CREATE TABLE IF NOT EXISTS etiquetas (
            id_etiqueta SERIAL PRIMARY KEY,
            nombre VARCHAR(40) NOT NULL UNIQUE
        );
        """,
        """
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
        """
    ]
    with engine.begin() as conn:
        if reiniciar:
            print("[Etapa 8 - DDL] Reiniciando tablas anteriores para carga limpia...")
            for d_stmt in drop_statements:
                conn.execute(text(d_stmt))
        for stmt in ddl_statements:
            conn.execute(text(stmt))
    print("[Etapa 8 - DDL] Tablas verificadas/creadas con éxito en PostgreSQL (Aiven).")

def cargar_a_postgres(engine, data_dict):
    print("\n[Etapa 8 - Carga] Insertando datos en base de datos en orden relacional...")
    with engine.begin() as conn:
        # Deshabilitar triggers temporalmente o insertar en orden de integridad
        print("  -> Insertando usuarios...")
        data_dict["usuarios"].to_sql("usuarios", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        
        print("  -> Insertando ubicaciones_usuario...")
        data_dict["ubicaciones_usuario"].to_sql("ubicaciones_usuario", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        
        print("  -> Insertando interacciones...")
        data_dict["interacciones"].to_sql("interacciones", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        
        print("  -> Insertando interacciones_no_vinculadas...")
        data_dict["interacciones_no_vinculadas"].to_sql("interacciones_no_vinculadas", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        
        print("  -> Insertando etiquetas...")
        data_dict["etiquetas"].to_sql("etiquetas", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        
        print("  -> Insertando interaccion_etiquetas...")
        data_dict["interaccion_etiquetas"].to_sql("interaccion_etiquetas", conn, if_exists="append", index=False, method="multi", chunksize=1000)

    print("[Etapa 8 - Carga] ¡Todos los datos fueron insertados exitosamente!")

def verificar_bd(engine):
    print("\n" + "=" * 65)
    print("      CONSULTAS DE AUDITORÍA Y VERIFICACIÓN EN AIVEN")
    print("=" * 65)
    tablas = ["usuarios", "ubicaciones_usuario", "interacciones", "interacciones_no_vinculadas", "etiquetas", "interaccion_etiquetas"]
    with engine.connect() as conn:
        for t in tablas:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {t};")).scalar()
            print(f"  * Total registros en tabla '{t}': {res}")
        
        # Validación de cumplimiento de privacidad
        violaciones = conn.execute(text("""
            SELECT COUNT(*) 
            FROM usuarios u 
            JOIN ubicaciones_usuario ub ON u.id_usuario = ub.id_usuario 
            WHERE u.consentimiento_datos = FALSE;
        """)).scalar()
        print(f"\n  [Auditoría Privacidad] Registros con consentimiento = FALSE en ubicaciones: {violaciones}")
        if violaciones == 0:
            print("  --> [OK] Cumplimiento estricto de privacidad validado (0 violaciones).")
        else:
            print("  --> [ALERTA] Se detectaron registros sin consentimiento en ubicaciones.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL Community 360")
    parser.add_argument("--uri", type=str, help="URI de conexión a PostgreSQL (Aiven)")
    parser.add_argument("--password", type=str, help="Contraseña de Aiven")
    parser.add_argument("--solo-limpieza", action="store_true", help="Solo ejecutar etapas 1 a 7")
    args = parser.parse_args()

    data = ejecutar_etl()

    if not args.solo_limpieza:
        db_uri = args.uri or os.getenv("AIVEN_DB_URI")
        password = args.password or os.getenv("AIVEN_DB_PASS", "")
        if db_uri or password:
            try:
                engine = get_db_engine(db_uri=db_uri)
                crear_tablas_postgres(engine)
                cargar_a_postgres(engine, data)
                verificar_bd(engine)
            except Exception as e:
                print(f"\n[Error en carga de BD]: {e}")
        else:
            print("\n[INFO] Para cargar directamente a Aiven, ejecute con:")
            print("  python etl_community360.py --password <TU_CONTRASENA_AIVEN>")
            print("  o defina la variable de entorno AIVEN_DB_PASS.")
