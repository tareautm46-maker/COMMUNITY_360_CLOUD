"""
COMMUNITY 360 - Backend API REST + WebSockets + JWT Authentication
Persistencia en Aiven Cloud (PostgreSQL 16)
Unidad III: Arquitectura de datos en la nube y consumo reactivo
"""

import os
import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import bcrypt
import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# =============================================================================
# CONFIGURACIÓN Y CONEXIÓN A BASE DE DATOS
# =============================================================================
# Cargar variables de entorno locales si existe archivo .env
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
except Exception:
    pass

DB_USER = os.getenv("AIVEN_DB_USER", "avnadmin")
DB_PASS = os.getenv("AIVEN_DB_PASS", "")
DB_HOST = os.getenv("AIVEN_DB_HOST", "pg-17441907-tareautm46-43ae.k.aivencloud.com")
DB_PORT = os.getenv("AIVEN_DB_PORT", "17635")
DB_NAME = os.getenv("AIVEN_DB_NAME", "defaultdb")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

engine = create_engine(DB_URL, poolclass=QueuePool, pool_size=10, max_overflow=20)

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_community360_key_2026_utm")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

app = FastAPI(
    title="COMMUNITY 360 - Cloud Data Architecture & Reactive WebSockets",
    description="Sistema web analítico de interacciones y gobernanza de datos para la Unidad III",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer(auto_error=False)

# =============================================================================
# GESTOR DE CONEXIONES WEBSOCKET (TIEMPO REAL)
# =============================================================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# =============================================================================
# MODELOS PYDANTIC
# =============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class InteractionCreate(BaseModel):
    id_interaccion: str = Field(..., example="I0009999")
    id_usuario: str = Field(..., example="U000001")
    canal: str = Field(..., example="discord")
    tipo: str = Field(..., example="mensaje")
    texto: str = Field(..., example="Participando en el nuevo evento de dibujo digital!")
    tema: str = Field(..., example="arte")
    sentimiento: float = Field(..., ge=-1.0, le=1.0, example=0.85)
    idioma: str = Field(default="es", example="es")
    dispositivo: str = Field(default="escritorio", example="escritorio")
    reacciones_recibidas: int = Field(default=0, ge=0, example=5)

class InteractionUpdate(BaseModel):
    canal: Optional[str] = None
    tipo: Optional[str] = None
    texto: Optional[str] = None
    tema: Optional[str] = None
    sentimiento: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    idioma: Optional[str] = None
    dispositivo: Optional[str] = None
    reacciones_recibidas: Optional[int] = Field(default=None, ge=0)

# =============================================================================
# SERVICIOS DE SEGURIDAD Y AUTENTICACIÓN
# =============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación no proporcionado. Inicie sesión para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token no contiene identidad de usuario")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# =============================================================================
# RUTAS DE AUTENTICACIÓN (FASE 3)
# =============================================================================
@app.post("/api/auth/login")
def login(creds: LoginRequest):
    with engine.connect() as conn:
        query = text("SELECT id_admin, username, password_hash, nombre_completo, rol, activo FROM usuarios_admin WHERE username = :u;")
        row = conn.execute(query, {"u": creds.username.strip()}).fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas: usuario no encontrado")
        
        id_admin, username, password_hash, nombre, rol, activo = row
        
        if not activo:
            raise HTTPException(status_code=403, detail="Cuenta administrativa suspendida")
        
        if not verify_password(creds.password, password_hash):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas: contraseña errónea")
        
        token = create_jwt_token({
            "sub": username,
            "id": id_admin,
            "nombre": nombre,
            "rol": rol
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": id_admin,
                "username": username,
                "nombre": nombre,
                "rol": rol
            }
        }

@app.get("/api/auth/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return {"status": "autenticado", "usuario": current_user}

# =============================================================================
# CONSULTAS ANALÍTICAS Y ESTADÍSTICAS EN VIVO (FASE 4 Y 6)
# =============================================================================
def obtener_metricas_en_vivo():
    with engine.connect() as conn:
        # Conteos y promedios
        total_interacciones = conn.execute(text("SELECT COUNT(*) FROM interacciones;")).scalar() or 0
        sentimiento_prom = conn.execute(text("SELECT ROUND(AVG(sentimiento)::numeric, 2) FROM interacciones;")).scalar() or 0.0
        total_usuarios = conn.execute(text("SELECT COUNT(*) FROM usuarios;")).scalar() or 0
        usuarios_consentimiento = conn.execute(text("SELECT COUNT(*) FROM ubicaciones_usuario;")).scalar() or 0
        total_huerfanos = conn.execute(text("SELECT COUNT(*) FROM interacciones_no_vinculadas;")).scalar() or 0
        
        # Desglose por canal
        canales_res = conn.execute(text("""
            SELECT canal, COUNT(*) AS total, ROUND(AVG(sentimiento)::numeric, 2) AS sentimiento
            FROM interacciones
            GROUP BY canal
            ORDER BY total DESC;
        """)).fetchall()
        
        canales = [
            {"canal": r[0].capitalize(), "total": r[1], "sentimiento": float(r[2] or 0.0)}
            for r in canales_res
        ]
        
        # Sentimientos
        sent_pos = conn.execute(text("SELECT COUNT(*) FROM interacciones WHERE sentimiento > 0.05;")).scalar() or 0
        sent_neu = conn.execute(text("SELECT COUNT(*) FROM interacciones WHERE sentimiento BETWEEN -0.05 AND 0.05;")).scalar() or 0
        sent_neg = conn.execute(text("SELECT COUNT(*) FROM interacciones WHERE sentimiento < -0.05;")).scalar() or 0
        
        # Top temas
        temas_res = conn.execute(text("""
            SELECT tema, COUNT(*) as total
            FROM interacciones
            GROUP BY tema
            ORDER BY total DESC
            LIMIT 5;
        """)).fetchall()
        temas = [{"tema": r[0].capitalize(), "total": r[1]} for r in temas_res]

        return {
            "total_interacciones": total_interacciones,
            "sentimiento_promedio": float(sentimiento_prom),
            "total_usuarios": total_usuarios,
            "usuarios_con_consentimiento": usuarios_consentimiento,
            "usuarios_sin_consentimiento": total_usuarios - usuarios_consentimiento,
            "interacciones_huerfanas_aisladas": total_huerfanos,
            "canales": canales,
            "sentimientos": {
                "positivo": sent_pos,
                "neutro": sent_neu,
                "negativo": sent_neg
            },
            "temas": temas,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

@app.get("/api/stats/summary")
def get_stats_summary():
    return obtener_metricas_en_vivo()

@app.get("/api/stats/channels")
def get_channel_stats():
    stats = obtener_metricas_en_vivo()
    return stats["canales"]

@app.get("/api/stats/sentiments")
def get_sentiment_stats():
    stats = obtener_metricas_en_vivo()
    return stats["sentimientos"]

# =============================================================================
# ENDPOINTS REST DE ADMINISTRACIÓN DE INTERACCIONES (FASE 4)
# Y NOTIFICACIÓN REACTIVA POR WEBSOCKETS (FASE 5)
# =============================================================================
@app.get("/api/interacciones")
def list_interacciones(limit: int = 50):
    with engine.connect() as conn:
        query = text("""
            SELECT i.id_interaccion, i.id_usuario, u.alias, i.timestamp, i.canal, i.tipo, 
                   i.texto, i.tema, i.sentimiento, i.reacciones_recibidas
            FROM interacciones i
            LEFT JOIN usuarios u ON i.id_usuario = u.id_usuario
            ORDER BY i.timestamp DESC
            LIMIT :lim;
        """)
        rows = conn.execute(query, {"lim": limit}).fetchall()
        
        resultado = []
        for r in rows:
            resultado.append({
                "id_interaccion": r[0],
                "id_usuario": r[1],
                "alias": r[2] or "Desconocido",
                "timestamp": str(r[3]),
                "canal": r[4],
                "tipo": r[5],
                "texto": r[6],
                "tema": r[7],
                "sentimiento": float(r[8]),
                "reacciones_recibidas": r[9]
            })
        return resultado

@app.get("/api/interacciones/{id_interaccion}")
def get_interaccion(id_interaccion: str):
    with engine.connect() as conn:
        query = text("""
            SELECT i.id_interaccion, i.id_usuario, u.alias, i.timestamp, i.canal, i.tipo, 
                   i.texto, i.tema, i.sentimiento, i.idioma, i.dispositivo, i.longitud_texto, i.reacciones_recibidas
            FROM interacciones i
            LEFT JOIN usuarios u ON i.id_usuario = u.id_usuario
            WHERE i.id_interaccion = :id;
        """)
        row = conn.execute(query, {"id": id_interaccion}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Interacción '{id_interaccion}' no encontrada.")
        
        return {
            "id_interaccion": row[0],
            "id_usuario": row[1],
            "alias": row[2] or "Desconocido",
            "timestamp": str(row[3]),
            "canal": row[4],
            "tipo": row[5],
            "texto": row[6],
            "tema": row[7],
            "sentimiento": float(row[8]),
            "idioma": row[9],
            "dispositivo": row[10],
            "longitud_texto": row[11],
            "reacciones_recibidas": row[12]
        }

@app.post("/api/interacciones", status_code=status.HTTP_201_CREATED)
async def create_interaccion(data: InteractionCreate):
    with engine.begin() as conn:
        # Validar existencia de usuario (Integridad Referencial)
        user_check = conn.execute(
            text("SELECT id_usuario FROM usuarios WHERE id_usuario = :uid;"),
            {"uid": data.id_usuario}
        ).fetchone()
        
        if not user_check:
            raise HTTPException(
                status_code=400,
                detail=f"Error de integridad referencial: El usuario '{data.id_usuario}' no existe en el catálogo maestro."
            )

        # Validar duplicado de clave primaria
        id_check = conn.execute(
            text("SELECT id_interaccion FROM interacciones WHERE id_interaccion = :iid;"),
            {"iid": data.id_interaccion}
        ).fetchone()
        if id_check:
            raise HTTPException(
                status_code=400,
                detail=f"La interacción '{data.id_interaccion}' ya existe."
            )

        ahora = datetime.datetime.now()
        long_txt = len(data.texto)

        insert_sql = text("""
            INSERT INTO interacciones (
                id_interaccion, id_usuario, timestamp, canal, tipo, texto, tema,
                sentimiento, idioma, dispositivo, longitud_texto, reacciones_recibidas
            ) VALUES (
                :iid, :uid, :ts, :canal, :tipo, :texto, :tema,
                :sent, :idioma, :disp, :long, :reac
            );
        """)
        conn.execute(insert_sql, {
            "iid": data.id_interaccion,
            "uid": data.id_usuario,
            "ts": ahora,
            "canal": data.canal.lower(),
            "tipo": data.tipo.lower(),
            "texto": data.texto,
            "tema": data.tema.lower(),
            "sent": round(data.sentimiento, 2),
            "idioma": data.idioma.lower(),
            "disp": data.dispositivo.lower(),
            "long": long_txt,
            "reac": data.reacciones_recibidas
        })

    # Notificación Reactiva por WebSockets
    metricas = obtener_metricas_en_vivo()
    payload = {
        "event": "INTERACTION_CREATED",
        "action": "create",
        "message": f"Nueva interacción registrada: {data.id_interaccion} en #{data.canal}",
        "interaction": {
            "id_interaccion": data.id_interaccion,
            "id_usuario": data.id_usuario,
            "canal": data.canal,
            "tipo": data.tipo,
            "texto": data.texto,
            "tema": data.tema,
            "sentimiento": data.sentimiento,
            "timestamp": ahora.strftime("%Y-%m-%d %H:%M:%S")
        },
        "stats": metricas
    }
    await manager.broadcast(payload)

    return {
        "status": "success",
        "message": "Interacción creada exitosamente y notificada por WebSockets en tiempo real.",
        "data": payload["interaction"]
    }

@app.put("/api/interacciones/{id_interaccion}")
async def update_interaccion(id_interaccion: str, data: InteractionUpdate):
    with engine.begin() as conn:
        exist = conn.execute(
            text("SELECT id_interaccion, id_usuario FROM interacciones WHERE id_interaccion = :id;"),
            {"id": id_interaccion}
        ).fetchone()
        
        if not exist:
            raise HTTPException(status_code=404, detail=f"Interacción '{id_interaccion}' no encontrada.")

        updates = []
        params = {"id": id_interaccion}

        if data.canal is not None:
            updates.append("canal = :canal")
            params["canal"] = data.canal.lower()
        if data.tipo is not None:
            updates.append("tipo = :tipo")
            params["tipo"] = data.tipo.lower()
        if data.texto is not None:
            updates.append("texto = :texto")
            params["texto"] = data.texto
            updates.append("longitud_texto = :long")
            params["long"] = len(data.texto)
        if data.tema is not None:
            updates.append("tema = :tema")
            params["tema"] = data.tema.lower()
        if data.sentimiento is not None:
            updates.append("sentimiento = :sent")
            params["sent"] = round(data.sentimiento, 2)
        if data.idioma is not None:
            updates.append("idioma = :idioma")
            params["idioma"] = data.idioma.lower()
        if data.dispositivo is not None:
            updates.append("dispositivo = :disp")
            params["disp"] = data.dispositivo.lower()
        if data.reacciones_recibidas is not None:
            updates.append("reacciones_recibidas = :reac")
            params["reac"] = data.reacciones_recibidas

        if not updates:
            return {"status": "no_changes", "message": "No se proporcionaron campos a actualizar."}

        sql = f"UPDATE interacciones SET {', '.join(updates)} WHERE id_interaccion = :id;"
        conn.execute(text(sql), params)

    metricas = obtener_metricas_en_vivo()
    payload = {
        "event": "INTERACTION_UPDATED",
        "action": "update",
        "message": f"Interacción {id_interaccion} actualizada desde Postman.",
        "id_interaccion": id_interaccion,
        "stats": metricas
    }
    await manager.broadcast(payload)

    return {"status": "success", "message": f"Interacción {id_interaccion} actualizada exitosamente.", "id": id_interaccion}

@app.delete("/api/interacciones/{id_interaccion}")
async def delete_interaccion(id_interaccion: str):
    with engine.begin() as conn:
        exist = conn.execute(
            text("SELECT id_interaccion FROM interacciones WHERE id_interaccion = :id;"),
            {"id": id_interaccion}
        ).fetchone()
        
        if not exist:
            raise HTTPException(status_code=404, detail=f"Interacción '{id_interaccion}' no encontrada.")

        conn.execute(text("DELETE FROM interaccion_etiquetas WHERE id_interaccion = :id;"), {"id": id_interaccion})
        conn.execute(text("DELETE FROM interacciones WHERE id_interaccion = :id;"), {"id": id_interaccion})

    metricas = obtener_metricas_en_vivo()
    payload = {
        "event": "INTERACTION_DELETED",
        "action": "delete",
        "message": f"Interacción {id_interaccion} eliminada desde Postman.",
        "id_interaccion": id_interaccion,
        "stats": metricas
    }
    await manager.broadcast(payload)

    return {"status": "success", "message": f"Interacción '{id_interaccion}' eliminada exitosamente."}

# =============================================================================
# ENDPOINT WEBSOCKET (FASE 5)
# =============================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Enviar estado actual inmediato
    stats = obtener_metricas_en_vivo()
    await websocket.send_json({
        "event": "CONNECTED",
        "message": "Conectado exitosamente al canal en tiempo real de Community 360",
        "stats": stats
    })
    try:
        while True:
            # Mantener conexión viva y procesar pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# =============================================================================
# RUTAS DE INTERFAZ WEB (FASE 3 Y 6)
# =============================================================================
@app.get("/", response_class=HTMLResponse)
def index_redirect():
    return RedirectResponse(url="/static/login.html")

@app.get("/login", response_class=HTMLResponse)
def serve_login():
    return RedirectResponse(url="/static/login.html")

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return RedirectResponse(url="/static/dashboard.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
