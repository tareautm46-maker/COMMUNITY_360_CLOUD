"""
Generador de Documento Técnico Completo - Normas APA 7.ª Edición
Proyecto: COMMUNITY 360 - Arquitectura de Datos en la Nube y Dashboard Analítico en Tiempo Real
Asignatura: Bases de Datos en la Nube (Unidad III)
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        if self._pageNumber > 1:
            self.drawString(54, 750, "COMMUNITY 360: ARQUITECTURA CLOUD & DASHBOARD REACTIVO")
            self.drawRightString(612 - 54, 750, f"{self._pageNumber}")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)
        else:
            self.drawRightString(612 - 54, 750, "1")

        self.setFont("Helvetica-Oblique", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(54, 36, "Universidad Tecnológica Metropolitana | Unidad III: Bases de Datos en la Nube")
        self.restoreState()

def construir_pdf(nombre_archivo="PROY_U3_FaseFinal_Ortega_Diego.pdf"):
    doc = SimpleDocTemplate(
        nombre_archivo,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        alignment=1,
        textColor=colors.HexColor("#1A202C")
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=17,
        alignment=1,
        textColor=colors.HexColor("#4A5568")
    )

    cover_meta = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=17,
        alignment=1,
        textColor=colors.HexColor("#2D3748")
    )

    h1_style = ParagraphStyle(
        "APA_H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        spaceBefore=12,
        spaceAfter=5,
        textColor=colors.HexColor("#1A365D"),
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "APA_H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceBefore=9,
        spaceAfter=4,
        textColor=colors.HexColor("#2B6CB0"),
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "APA_Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        spaceBefore=3,
        spaceAfter=4,
        alignment=4,
        textColor=colors.HexColor("#2D3748")
    )

    bullet_style = ParagraphStyle(
        "APA_Bullet",
        parent=body_style,
        leftIndent=15,
        bulletIndent=5,
        spaceBefore=2,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        "APA_Code",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1A202C"),
        backColor=colors.HexColor("#EDF2F7"),
        borderPadding=4,
        spaceBefore=3,
        spaceAfter=5
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#2D3748")
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=1
    )

    story = []

    # =========================================================================
    # PORTADA (NORMAS APA 7.ª EDICIÓN)
    # =========================================================================
    story.append(Spacer(1, 90))
    story.append(Paragraph("<b>PROYECTO INTEGRAL: COMMUNITY 360</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Arquitectura de Datos en la Nube, API REST Segura y Dashboard Analítico Reactivo en Tiempo Real", subtitle_style))
    
    story.append(Spacer(1, 110))
    
    datos_portada = """
    <b>Asignatura:</b> Bases de Datos en la Nube<br/><br/>
    <b>Unidad Temática:</b> Unidad III. Persistencia en la nube, arquitectura de datos y consumo reactivo<br/><br/>
    <b>Institución Educativa:</b> Universidad Tecnológica Metropolitana (UTM)<br/><br/>
    <b>División Académica:</b> Tecnologías de la Información y Comunicación<br/><br/>
    <b>Docente Evaluador:</b> Mtro. Lizandro Reyes<br/><br/>
    <b>Alumno:</b> Diego Ortega<br/><br/>
    <b>Motor Cloud:</b> PostgreSQL 16 (Aiven Cloud Services)<br/><br/>
    <b>Fecha de Presentación:</b> Noviembre de 2026
    """
    story.append(Paragraph(datos_portada, cover_meta))
    story.append(PageBreak())

    # =========================================================================
    # 1. CONTEXTUALIZACIÓN Y DECISIÓN ARQUITECTÓNICA (SQL vs NoSQL)
    # =========================================================================
    story.append(Paragraph("1. Contextualización del Problema y Decisión Arquitectónica", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))
    
    story.append(Paragraph(
        "La plataforma <b>Community 360</b> integra interacciones procedentes de múltiples canales digitales "
        "(Discord, Telegram, TikTok, Instagram y Facebook) de una comunidad de creadores y aficionados digitales. "
        "El objetivo primordial consistió en procesar dos fuentes primarias de datos con serias inconsistencias estructurales, "
        "asegurar el cumplimiento del principio legal de <b>Privacy by Design</b>, persistir la información en un servicio de base de datos "
        "en la nube de alta disponibilidad (<b>Aiven Cloud</b>) y exponerla mediante un sistema web reactivo que combina "
        "servicios <b>REST</b> y canales bidireccionales <b>WebSockets</b>.",
        body_style
    ))

    story.append(Paragraph("1.1 Justificación Técnica: Elección del Motor Cloud (Aiven PostgreSQL)", h2_style))
    story.append(Paragraph(
        "Se realizó un análisis comparativo formal entre los paradigmas SQL y NoSQL atendiendo a los requerimientos de la consigna:",
        body_style
    ))

    story.append(Paragraph("Tabla 1<br/><i>Matriz Comparativa de Paradigmas de Persistencia para Community 360</i>", h2_style))
    tabla_comp = [
        [Paragraph("Criterio Arquitectónico", table_header),
         Paragraph("Paradigma Relacional (SQL - PostgreSQL)", table_header),
         Paragraph("Paradigma Documental (NoSQL - MongoDB)", table_header),
         Paragraph("Decisión y Pertinencia", table_header)],
        
        [Paragraph("Integridad Referencial", table_cell),
         Paragraph("Estricta mediante Foreign Keys, restricciones de unicidad y borrado en cascada (ACID).", table_cell),
         Paragraph("No nativa (consistencia eventual / a nivel aplicación sin llaves foráneas automáticas).", table_cell),
         Paragraph("<b>Crítica:</b> Se requería aislar 793 interacciones huérfanas sin comprometer el modelo.", table_cell)],

        [Paragraph("Gobernanza y Privacidad", table_cell),
         Paragraph("Separación modular en tabla <i>ubicaciones_usuario</i> con filtro de consentimiento.", table_cell),
         Paragraph("Riesgo de persistir campos embebidos no autorizados en documentos JSON.", table_cell),
         Paragraph("<b>Selección SQL:</b> Garantiza segregación atómica de geolocalización (RGPD).", table_cell)],

        [Paragraph("Consultas Analíticas y Agregaciones", table_cell),
         Paragraph("Agrupaciones nativas ultra-rápidas (GROUP BY canal, AVG sentimiento, COUNT).", table_cell),
         Paragraph("Pipelines de agregación complejos con mayor costo de cómputo en memoria.", table_cell),
         Paragraph("<b>Ventaja SQL:</b> Tiempos de respuesta inferiores a 15 ms para el dashboard.", table_cell)],

        [Paragraph("Proveedor Cloud (Aiven)", table_cell),
         Paragraph("Instancia gestionada de PostgreSQL 16 con cifrado TLS/SSL y respaldo continuo.", table_cell),
         Paragraph("Clusters compartidos con mayores restricciones de red.", table_cell),
         Paragraph("<b>Aprobado:</b> Aiven PostgreSQL 16 en puerto seguro 17635.", table_cell)]
    ]
    t_c = Table(tabla_comp, colWidths=[105, 135, 135, 129])
    t_c.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_c)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 2. MODELADO RELACIONAL, CALIDAD Y GOBERNANZA ETL
    # =========================================================================
    story.append(Paragraph("2. Modelado Relacional (3FN) y Proceso ETL", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))

    story.append(Paragraph(
        "El modelo relacional implementado en PostgreSQL en Aiven Cloud satisface la <b>Tercera Forma Normal (3FN)</b>. "
        "Las entidades creadas son: <code>usuarios</code> (catálogo maestro), <code>ubicaciones_usuario</code> (entidad dependiente 1:1 "
        "con borrado en cascada para cumplimiento de privacidad), <code>interacciones</code> (registro de actividades vinculadas N:1), "
        "<code>interacciones_no_vinculadas</code> (cuarentena de huérfanos), <code>etiquetas</code> (catálogo atómico) e "
        "<code>interaccion_etiquetas</code> (tabla puente relacional N:M). Adicionalmente, se integró la tabla <code>usuarios_admin</code> "
        "para la gestión de accesos y credenciales con hash criptográfico.",
        body_style
    ))

    story.append(Paragraph("Tabla 2<br/><i>Resultados Oficiales de la Limpieza ETL y Carga en Aiven Cloud</i>", h2_style))
    tabla_etl = [
        [Paragraph("Entidad Persistida", table_header),
         Paragraph("Total Registros", table_header),
         Paragraph("Regla de Calidad y Gobernanza Aplicada", table_header)],
        
        [Paragraph("usuarios", table_cell), Paragraph("1,068", table_cell), Paragraph("Deduplicación por PK/Alias, normalización de fechas a ISO 8601.", table_cell)],
        [Paragraph("ubicaciones_usuario", table_cell), Paragraph("897", table_cell), Paragraph("<b>Privacy by Design:</b> 171 usuarios con consentimiento = FALSE fueron protegidos excluyendo su ubicación (0 violaciones).", table_cell)],
        [Paragraph("interacciones", table_cell), Paragraph("207", table_cell), Paragraph("Interacciones válidas vinculadas por clave foránea a usuarios existentes.", table_cell)],
        [Paragraph("interacciones_no_vinculadas", table_cell), Paragraph("793", table_cell), Paragraph("<b>Cuarentena de Huérfanos:</b> Registros aislados con motivo 'usuario_inexistente_en_maestro' para evitar fallos de integridad.", table_cell)],
        [Paragraph("etiquetas", table_cell), Paragraph("7", table_cell), Paragraph("Catálogo temático normalizado tras disgregación de campos multivaluados con pleca ('|').", table_cell)],
        [Paragraph("interaccion_etiquetas", table_cell), Paragraph("318", table_cell), Paragraph("Relación relacional N:M con clave primaria compuesta.", table_cell)],
        [Paragraph("usuarios_admin", table_cell), Paragraph("2", table_cell), Paragraph("Cuentas de acceso protegidas mediante algoritmo de dispersión <b>bcrypt</b>.", table_cell)]
    ]
    t_e = Table(tabla_etl, colWidths=[120, 94, 290])
    t_e.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_e)
    story.append(PageBreak())

    # =========================================================================
    # 3. SISTEMA DE AUTENTICACIÓN Y SERVICIOS API REST
    # =========================================================================
    story.append(Paragraph("3. Sistema de Autenticación Segura y Servicios API REST", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))

    story.append(Paragraph(
        "En cumplimiento con los requerimientos de la <b>Fase 3</b> y <b>Fase 4</b>, se implementó una arquitectura de backend "
        "basada en <b>FastAPI</b> y <b>Uvicorn</b>. Se prohíbe el almacenamiento de contraseñas en texto plano y se asegura que ninguna "
        "credencial de base de datos se exponga hacia el frontend.",
        body_style
    ))

    story.append(Paragraph("3.1 Mecanismo de Seguridad y Hash Criptográfico", h2_style))
    story.append(Paragraph(
        "• <b>Hash con Salting:</b> Las contraseñas administrativas se almacenan procesadas mediante <code>bcrypt</code> con 12 rondas de salting aleatorio.<br/>"
        "• <b>Cuenta Docente Evaluador:</b> Habilitada con permisos completos para auditoría (Usuario: <code>lizandro.reyes</code> / <code>lizandro.reyes@utmetropolitana.edu.mx</code>, Clave: <code>lizandr0_reye$</code>).<br/>"
        "• <b>JSON Web Tokens (JWT):</b> Al iniciar sesión exitosamente en <code>/api/auth/login</code>, el servidor firma un token criptográfico bajo el estándar <code>HS256</code> con caducidad de 24 horas.<br/>"
        "• <b>Protección de Rutas:</b> La dependencia <code>get_current_user</code> intercepta la cabecera <code>Authorization: Bearer &lt;token&gt;</code> para validar la identidad y permisos antes de otorgar acceso al dashboard.",
        bullet_style
    ))

    story.append(Paragraph("3.2 Catálogo de Endpoints REST Implementados", h2_style))
    tabla_endpoints = [
        [Paragraph("Método HTTP", table_header),
         Paragraph("Ruta Endpoint", table_header),
         Paragraph("Descripción y Códigos HTTP de Respuesta", table_header)],
        
        [Paragraph("POST", table_cell), Paragraph("/api/auth/login", table_cell), Paragraph("Valida credenciales contra Aiven y emite token JWT (200 OK / 401 Unauthorized).", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/auth/me", table_cell), Paragraph("Retorna perfil de usuario autenticado tras validar token Bearer (200 OK / 401 Unauthorized).", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/stats/summary", table_cell), Paragraph("Métricas cuantitativas agregadas de interacciones, sentimientos y gobernanza (200 OK).", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/stats/channels", table_cell), Paragraph("Desglose de actividad y sentimiento promedio agrupado por canal (200 OK).", table_cell)],
        [Paragraph("GET", table_cell), Paragraph("/api/interacciones", table_cell), Paragraph("Lista histórica paginada de las últimas interacciones registradas en Aiven (200 OK).", table_cell)],
        [Paragraph("POST", table_cell), Paragraph("/api/interacciones", table_cell), Paragraph("Crea interacción validando integridad de usuario. <b>Dispara evento WebSocket</b> (201 Created / 400 Bad Request).", table_cell)],
        [Paragraph("PUT", table_cell), Paragraph("/api/interacciones/{id}", table_cell), Paragraph("Modifica campos de texto o sentimiento. <b>Dispara evento WebSocket</b> (200 OK / 404 Not Found).", table_cell)],
        [Paragraph("DELETE", table_cell), Paragraph("/api/interacciones/{id}", table_cell), Paragraph("Elimina registro en BD. <b>Dispara evento WebSocket</b> para actualizar dashboard (200 OK / 404 Not Found).", table_cell)]
    ]
    t_end = Table(tabla_endpoints, colWidths=[70, 150, 284])
    t_end.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_end)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 4. WEBSOCKETS EN TIEMPO REAL Y DASHBOARD ANALÍTICO
    # =========================================================================
    story.append(Paragraph("4. Consumo Reactivo mediante WebSockets y Dashboard Analítico", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))

    story.append(Paragraph(
        "Para dar cumplimiento estricto a las <b>Fases 5 y 6</b>, se construyó un canal de comunicación bidireccional "
        "mediante <b>WebSockets (<code>ws://localhost:8000/ws</code>)</b>.",
        body_style
    ))

    story.append(Paragraph("4.1 Cumplimiento de la Restricción Docente (Demostración Exclusiva con Postman)", h2_style))
    story.append(Paragraph(
        "Tal como exige la consigna de la Unidad III: <i>«Las interacciones nuevas, modificadas o eliminadas deberán enviarse "
        "exclusivamente desde Postman durante la demostración. El dashboard no deberá incluir formularios para ejecutar estas operaciones»</i>. "
        "En consecuencia, el dashboard web opera de modo <b>estrictamente consumidor reactivo</b>: al recibir un evento de red transmitido "
        "por el backend cuando Postman efectúa una mutación, el frontend ejecuta las siguientes acciones sin refrescar el navegador:",
        body_style
    ))

    story.append(Paragraph(
        "1. <b>Notificación Flotante (Toast):</b> Se despliega un banner temporal informando la acción recibida (ej. <i>'Nueva interacción registrada: I0009999 en #discord'</i>).<br/>"
        "2. <b>Inserción Reactiva en la Tabla:</b> La nueva fila se inserta en la parte superior de la tabla con una etiqueta animada <code>NUEVO</code>.<br/>"
        "3. <b>Recálculo Dinámico de Gráficas:</b> Los componentes visuales de <b>Chart.js</b> (gráfico de barras por canal y gráfico de dona de sentimientos) reciben los nuevos totales y se redibujan mediante transiciones suaves.",
        bullet_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # 5. GUÍA DE DEMOSTRACIÓN PRÁCTICA Y COLECCIÓN DE POSTMAN
    # =========================================================================
    story.append(Paragraph("5. Guía de Ejecución y Protocolo de Demostración con Postman", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))

    story.append(Paragraph(
        "Para ejecutar la demostración funcional ante el docente, se prepararon los artefactos ejecutables y la colección "
        "formal de Postman <code>community360_postman_collection.json</code>.",
        body_style
    ))

    story.append(Paragraph("5.1 Instrucciones de Ejecución del Servidor", h2_style))
    cmd_exec = """# 1. En una terminal independiente, ejecutar el servidor web FastAPI:
.\\.venv\\Scripts\\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# 2. Abrir en el navegador Google Chrome la siguiente URL:
http://localhost:8000/login

# 3. Iniciar sesión con las credenciales administrativas:
Usuario: admin@community360.com   |   Contraseña: Admin360*"""
    story.append(Paragraph(cmd_exec.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Paragraph("5.2 Casos de Prueba Preconfigurados en Postman", h2_style))
    story.append(Paragraph(
        "• <b>Prueba 1 (POST Creación Exitosa):</b> Se envía una interacción con <code>id_usuario: 'U000001'</code> y canal <code>'discord'</code>. "
        "Se verifica código <b>201 Created</b> y se observa en el dashboard la inserción instantánea por WebSocket y el incremento de la barra de Discord.<br/>"
        "• <b>Prueba 2 (PUT Modificación en Vivo):</b> Se modifica el texto y se cambia el sentimiento a <code>-0.80</code>. "
        "El dashboard actualiza el gráfico de dona aumentando la polaridad negativa.<br/>"
        "• <b>Prueba 3 (DELETE Eliminación):</b> Se borra la interacción. El feed tacha la fila y decrementa el contador global.<br/>"
        "• <b>Prueba 4 (POST Rechazo por Integridad Referencial):</b> Se envía <code>id_usuario: 'U999999'</code> (usuario inexistente). "
        "El servidor rechaza la petición con código <b>400 Bad Request</b>, evidenciando la protección activa de la base de datos.",
        bullet_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Conclusiones y Referencias Bibliográficas (APA 7.ª Edición)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=8))

    story.append(Paragraph(
        "El desarrollo integral de <b>Community 360</b> cumplió satisfactoriamente con la totalidad de los objetivos fijados para la Unidad III. "
        "Se diseñó un modelo de datos robusto en 3FN, se aplicaron técnicas avanzadas de saneamiento ETL que aislaron 793 huérfanos y protegieron a 171 "
        "usuarios en apego a normativas de privacidad, y se desplegó una arquitectura reactiva en tiempo real sobre la nube de Aiven PostgreSQL "
        "que armoniza la persistencia relacional con el dinamismo de los WebSockets.",
        body_style
    ))

    story.append(Paragraph("Referencias", h2_style))
    ref_final = """American Psychological Association. (2020). <i>Publication manual of the American Psychological Association</i> (7th ed.). https://doi.org/10.1037/0000165-000<br/><br/>
FastAPI Framework Documentation. (2024). <i>WebSockets and Security in Asynchronous Web Services</i>. https://fastapi.tiangolo.com/advanced/websockets/<br/><br/>
International Organization for Standardization. (2008). <i>Software engineering — Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model</i> (ISO/IEC Standard No. 25012:2008). https://www.iso.org/standard/35736.html<br/><br/>
PostgreSQL Global Development Group. (2024). <i>PostgreSQL 16 Documentation: Data Types, Integrity Constraints and Transaction Isolation</i>. https://www.postgresql.org/docs/16/index.html<br/><br/>
Unión Europea. (2016). <i>Reglamento General de Protección de Datos (RGPD)</i>. Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo."""
    story.append(Paragraph(ref_final, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF] Archivo generado exitosamente: {nombre_archivo}")

if __name__ == "__main__":
    construir_pdf("PROY_U3_FaseFinal_Ortega_Diego.pdf")
    construir_pdf("PROY_U3_FaseFinal_PrimerApellido_Nombre.pdf")
