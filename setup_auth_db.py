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
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

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
        print("Sembrando usuarios administrativos por defecto...")
        pwd_hash = hash_password("Admin360*")
        pwd_docente_hash = hash_password("lizandr0_reye$")
        
        insert_stmt = text("""
            INSERT INTO usuarios_admin (username, password_hash, nombre_completo, rol, activo)
            VALUES 
                (:u1, :h1, :n1, :r1, TRUE),
                (:u2, :h1, :n2, :r1, TRUE),
                (:u3, :h2, :n3, 'docente_evaluador', TRUE),
                (:u4, :h2, :n3, 'docente_evaluador', TRUE)
            ON CONFLICT (username) DO UPDATE 
            SET password_hash = EXCLUDED.password_hash,
                nombre_completo = EXCLUDED.nombre_completo,
                activo = TRUE;
        """)
        conn.execute(insert_stmt, {
            "u1": "admin@community360.com", "h1": pwd_hash, "n1": "Diego Ortega (Admin)", "r1": "administrador",
            "u2": "admin", "n2": "Administrador General",
            "u3": "lizandro.reyes", "h2": pwd_docente_hash, "n3": "Mtro. Lizandro Reyes (Docente Evaluador)",
            "u4": "lizandro.reyes@utmetropolitana.edu.mx"
        })
        print("[OK] Usuarios sembrados exitosamente:")
        print("  - Docente: 'lizandro.reyes' / 'lizandro.reyes@utmetropolitana.edu.mx' (Clave: lizandr0_reye$)")
        print("  - Alumno: 'admin@community360.com' (Clave: Admin360*)")

if __name__ == "__main__":
    init_auth_table()
