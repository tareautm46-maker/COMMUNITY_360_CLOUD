"""
Configuración de la tabla de autenticación en PostgreSQL (Aiven)
Proyecto: COMMUNITY 360 - Fase 3 (Sistema de Autenticación)
"""

import os
import bcrypt
from sqlalchemy import create_engine, text

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def get_engine():
    user = os.getenv("AIVEN_DB_USER", "avnadmin")
    password = os.getenv("AIVEN_DB_PASS", "")
    host = os.getenv("AIVEN_DB_HOST", "pg-17441907-tareautm46-43ae.k.aivencloud.com")
    port = os.getenv("AIVEN_DB_PORT", "17635")
    db_name = os.getenv("AIVEN_DB_NAME", "defaultdb")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"
    return create_engine(url)

def init_auth_table():
    engine = get_engine()
    print("Conectando a Aiven PostgreSQL para crear tabla de autenticación...")

    ddl = """
    CREATE TABLE IF NOT EXISTS usuarios_admin (
        id_admin SERIAL PRIMARY KEY,
        username VARCHAR(80) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        nombre_completo VARCHAR(120) NOT NULL,
        rol VARCHAR(30) NOT NULL DEFAULT 'administrador',
        activo BOOLEAN NOT NULL DEFAULT TRUE,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_usuarios_admin_username ON usuarios_admin (username);
    """

    with engine.begin() as conn:
        conn.execute(text(ddl))
        print("[OK] Tabla 'usuarios_admin' creada/verificada exitosamente.")

        # Verificar si existen usuarios admin
        count = conn.execute(text("SELECT COUNT(*) FROM usuarios_admin;")).scalar()
        if count == 0:
            print("Sembrando usuarios administrativos por defecto...")
            pwd_hash = hash_password("Admin360*")
            
            insert_stmt = text("""
                INSERT INTO usuarios_admin (username, password_hash, nombre_completo, rol, activo)
                VALUES 
                    (:u1, :h1, :n1, :r1, TRUE),
                    (:u2, :h2, :n2, :r2, TRUE);
            """)
            conn.execute(insert_stmt, {
                "u1": "admin@community360.com", "h1": pwd_hash, "n1": "Diego Ortega (Admin)", "r1": "administrador",
                "u2": "admin", "h2": pwd_hash, "n2": "Administrador General", "r2": "administrador"
            })
            print("[OK] Usuarios administradores sembrados: 'admin@community360.com' y 'admin' (Clave: Admin360*).")
        else:
            print(f"[INFO] Ya existen {count} administradores registrados en la base de datos.")

if __name__ == "__main__":
    init_auth_table()
