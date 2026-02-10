from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from dateutil.relativedelta import relativedelta
from xhtml2pdf import pisa
from io import BytesIO
from flask import make_response
from datetime import datetime, date, timedelta
import os
import win32com.client
import tempfile
import pythoncom
from db import get_connection

base_servidores_bp = Blueprint("base_servidores", __name__)

# ==========================
# CONFIGURACIÓN
# ==========================
SHEET_NAME = "BASE_SERVERS"

DESTINATARIOS_POR_LOCALIDAD = {
    "QUERETARO": [
        "ibm_qrcs_engineering-dg@ibm.com",
        "fvargas@mx1.ibm.com",
        "saguilar@mx1.ibm.com",
        "garcizam@mx1.ibm.com",
        "agomsan@mx1.ibm.com",
    ],
    "TULTITLAN": [
        "soporte.tulti@empresa.com",
        "infraestructura.tulti@empresa.com",
    ]
}

# ==========================
# UTILIDADES
# ==========================
def obtener_servidor_por_serie(serie):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            serie,
            hostname,
            marca,
            modelo,
            garantia AS fecha_garantia
        FROM base_servers
        WHERE serie = %s
        LIMIT 1
    """

    cursor.execute(query, (serie,))
    servidor = cursor.fetchone()

    cursor.close()
    conn.close()

    return servidor

def servidor_existe(serie, localidad):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 1
        FROM base_servers
        WHERE serie = %s AND localidad = %s
        LIMIT 1
    """, (serie, localidad))

    existe = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return existe


def buscar_servidor_mysql(termino, localidad):
    conn = get_connection()
    resultado = {"encontrado": False}

    if not conn:
        return resultado

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT serie, hostname, ubicacion, marca, modelo,
                   garantia, tipo_csp, modelo_csp, localidad, estatus
            FROM base_servers
            WHERE localidad = %s
              AND (serie = %s OR hostname = %s)
            """,
            (localidad, termino, termino)
        )

        row = cursor.fetchone()
        if row:
            # Convertir garantia a formatos RAW y VIEW
            garantia_raw = None
            garantia_view = None
            if row["garantia"]:
                garantia_raw = row["garantia"].strftime("%Y-%m-%d")
                garantia_view = row["garantia"].strftime("%d/%m/%Y")

            resultado = {
                "encontrado": True,
                "serie": row["serie"],
                "hostname": row["hostname"],
                "ubicacion": row["ubicacion"],
                "marca": row["marca"],
                "modelo": row["modelo"],
                "garantia_raw": garantia_raw,
                "garantia_view": garantia_view,
                "tipo_csp": row["tipo_csp"],
                "modelo_csp": row["modelo_csp"],
                "localidad": row["localidad"],
                "estatus": row["estatus"] if row["estatus"] else "ACTIVO",
            }

    except Exception as e:
        print("Error en buscar_servidor_mysql:", e)

    finally:
        cursor.close()
        conn.close()

    return resultado

def obtener_servidores_por_garantia(estado, localidad):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    hoy = date.today()
    limite = hoy + timedelta(days=30)

    if estado == "EN_GARANTIA":
        query = """
            SELECT *
            FROM base_servers
            WHERE localidad = %s
              AND garantia >= %s
            ORDER BY garantia
        """
        params = (localidad, hoy)

    elif estado == "POR_VENCER":
        query = """
            SELECT *
            FROM base_servers
            WHERE localidad = %s
              AND garantia BETWEEN %s AND %s
            ORDER BY garantia
        """
        params = (localidad, hoy, limite)

    else:  # VENCIDA
        query = """
            SELECT *
            FROM base_servers
            WHERE localidad = %s
              AND garantia < %s
            ORDER BY garantia DESC
        """
        params = (localidad, hoy)

    cursor.execute(query, params)
    servidores = cursor.fetchall()

    cursor.close()
    conn.close()

    return servidores

def generar_pdf(html):
    result = BytesIO()
    pisa.CreatePDF(
        src=html,
        dest=result,
        encoding="utf-8"
    )
    return result.getvalue()

def enviar_pdf_outlook(asunto, cuerpo_html, pdf_bytes, nombre_pdf, destinatarios=""):
    pythoncom.CoInitialize()  # ← OBLIGATORIO

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)

        mail.Subject = asunto
        mail.HTMLBody = cuerpo_html
        mail.To = destinatarios

        # Adjuntar PDF temporal
        temp_path = os.path.join(os.environ["TEMP"], nombre_pdf)
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)

        mail.Attachments.Add(temp_path)
        mail.Display()  # NO enviar automático (buena práctica)

    finally:
        pythoncom.CoUninitialize()  # ← OBLIGATORIO

# ==========================
# ENDPOINTS
# ==========================

@base_servidores_bp.route("/base-servidores", methods=["GET"])
def base_servidores():
    return render_template("Base_Servidores.html")

# -------------------------
# BUSQUEDA AJAX / JSON
# -------------------------
@base_servidores_bp.route("/base-servidores/buscar", methods=["GET"])
def buscar():
    termino = request.args.get("termino", "").strip()
    localidad = request.args.get("localidad", "").strip()
    if not termino or not localidad:
        return jsonify({"encontrado": False})

    return jsonify(buscar_servidor_mysql(termino, localidad))

# -------------------------
# REGISTRO NUEVO
# -------------------------
@base_servidores_bp.route("/base-servidores/nuevo", methods=["GET", "POST"])
def nuevo_servidor():
    if request.method == "POST":
        localidad = request.form.get("localidad", "").strip().upper()
        serie = request.form.get("serie", "").strip().upper()
        hostname = request.form.get("hostname", "").strip().upper()
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        ubicacion = request.form.get("ubicacion", "").strip()
        tipo_csp = request.form.get("tipo_csp", "").strip()
        modelo_csp = request.form.get("modelo_csp", "").strip()
        garantia_str = request.form.get("garantia", "").strip()
        estatus = "ACTIVO"

        if not serie or not localidad:
            flash("Serie y Localidad son obligatorias", "danger")
            return redirect(request.url)

        garantia = None
        if garantia_str:
            try:
                garantia = datetime.strptime(garantia_str, "%Y-%m-%d").date()
            except ValueError:
                garantia = None

        conn = get_connection()
        if not conn:
            flash("Error de conexión a MySQL", "danger")
            return redirect(request.url)

        try:
            cursor = conn.cursor()
            # Verificar duplicado
            cursor.execute(
                "SELECT 1 FROM base_servers WHERE serie=%s AND localidad=%s",
                (serie, localidad)
            )
            if cursor.fetchone():
                flash("El servidor ya existe en esta localidad", "warning")
                return redirect(request.url)

            # Insertar nuevo servidor
            cursor.execute(
                """
                INSERT INTO base_servers
                (serie, hostname, ubicacion, marca, modelo, garantia,
                 tipo_csp, modelo_csp, localidad, estatus)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (serie, hostname, ubicacion, marca, modelo, garantia,
                 tipo_csp, modelo_csp, localidad, estatus)
            )
            conn.commit()
            flash("Servidor registrado correctamente", "success")
            return redirect(url_for("base_servidores.base_servidores"))

        finally:
            cursor.close()
            conn.close()

    return render_template("Base_Servidores_Nuevo.html")

# -------------------------
# EDICIÓN
# -------------------------
@base_servidores_bp.route("/base-servidores/editar/<serie>", methods=["GET", "POST"])
def editar_servidor(serie):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔎 Obtener servidor real (fuente única de verdad)
    cursor.execute(
        "SELECT * FROM base_servers WHERE serie=%s",
        (serie,)
    )
    servidor = cursor.fetchone()

    if not servidor:
        cursor.close()
        conn.close()
        flash("Servidor no encontrado", "warning")
        return redirect(url_for("base_servidores.base_servidores"))

    if request.method == "POST":
        ubicacion = request.form.get("ubicacion", "").strip()
        estatus = request.form.get("estatus", "").strip()
        localidad = request.form.get("localidad", "").strip().upper()
        garantia_str = request.form.get("garantia", "").strip()


        garantia = None
        if garantia_str:
            try:
                garantia = datetime.strptime(garantia_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Formato de fecha incorrecto", "warning")
                return redirect(url_for("base_servidores.editar_servidor", serie=serie))

        try:
            cursor.execute(
                """
                UPDATE base_servers
                SET ubicacion=%s,
                    estatus=%s,
                    garantia=%s,
                    localidad=%s
                WHERE serie=%s
                """,
                (ubicacion, estatus, garantia, localidad, serie)
            )
            conn.commit()

            if cursor.rowcount:
                flash("Servidor actualizado correctamente", "success")
            else:
                flash("No se realizaron cambios", "warning")

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("base_servidores.editar_servidor", serie=serie))

    # GET → preparar datos para el template
    if servidor.get("garantia"):
        servidor["garantia"] = servidor["garantia"].strftime("%Y-%m-%d")
    else:
        servidor["garantia"] = ""

    cursor.close()
    conn.close()

    return render_template("editar_servidor.html", servidor=servidor)

# -------------------------
# ELIMINACIÓN
# -------------------------
@base_servidores_bp.route("/base-servidores/eliminar/<serie>", methods=["POST"])
def eliminar_servidor(serie):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM base_servers WHERE serie=%s",
            (serie,)
        )
        conn.commit()

        if cursor.rowcount:
            flash("Servidor eliminado correctamente", "success")
        else:
            flash("Servidor no encontrado", "warning")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("base_servidores.base_servidores"))
# -------------------------
# BÚSQUEDA DINÁMICA estilo Crear_Caso
# -------------------------
@base_servidores_bp.route("/base-servidores/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "").strip().upper()
    localidad = request.args.get("localidad", "").strip().upper()
    if not query or not localidad:
        return jsonify([])

    conn = get_connection()
    if not conn:
        return jsonify([])

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT serie, hostname
            FROM base_servers
            WHERE localidad=%s AND (UPPER(serie) LIKE %s OR UPPER(hostname) LIKE %s)
            ORDER BY serie
            LIMIT 10
            """,
            (localidad, f"%{query}%", f"%{query}%")
        )
        rows = cursor.fetchall()
        results = [{"serie": row[0], "hostname": row[1]} for row in rows]
        return jsonify(results)
    finally:
        cursor.close()
        conn.close()

@base_servidores_bp.route("/base-servidores/garantias/reporte")
def reporte_garantias():

    estado = request.args.get("estado", "EN_GARANTIA")
    localidad = request.args.get("localidad", "").strip()

    if not localidad:
        return redirect(url_for("base_servidores.selector_garantias"))

    servidores = obtener_servidores_por_garantia(estado, localidad)

    titulos = {
        "EN_GARANTIA": "Servidores en Garantía",
        "POR_VENCER": "Servidores con Garantía por Vencer",
        "VENCIDA": "Servidores con Garantía Vencida"
    }

    return render_template(
        "Base_Servidores_Garantias.html",
        servidores=servidores,
        estado=estado,
        localidad=localidad,
        titulo=f"{titulos.get(estado, 'Reporte de Garantías')} – {localidad}"
    )

@base_servidores_bp.route("/base-servidores/garantias/pdf")
def reporte_garantias_pdf():
    estado = request.args.get("estado", "EN_GARANTIA")
    localidad = request.args.get("localidad", "").strip()
    
    if not localidad:
        return "Localidad no especificada", 400

    servidores = obtener_servidores_por_garantia(estado, localidad)           
    
    titulo = {
        "EN_GARANTIA": "En Garantía",
        "POR_VENCER": "Por Vencer",
        "VENCIDA": "Fuera de Garantía"
    }.get(estado, "Reporte")

    html = render_template(
        "reporte_garantias_pdf.html",
        servidores=servidores,
        titulo=titulo,
        fecha=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    pdf = generar_pdf(html)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'attachment; filename=reporte_garantias_{estado}.pdf'
    )

    return response

@base_servidores_bp.route("/base-servidores/garantias/email")
def enviar_reporte_garantias_email():

    estado = request.args.get("estado", "EN_GARANTIA")
    localidad = request.args.get("localidad", "").strip().upper()

    if not localidad:
        flash("Debe seleccionar una localidad", "warning")
        return redirect(url_for("base_servidores.reporte_garantias", estado=estado))

    servidores = obtener_servidores_por_garantia(estado, localidad)

    lista = DESTINATARIOS_POR_LOCALIDAD.get(localidad, [])
    destinatarios = ";".join(lista)

    if not destinatarios:
        flash(f"No hay destinatarios configurados para {localidad}", "warning")
        return redirect(
            url_for("base_servidores.reporte_garantias", estado=estado, localidad=localidad)
        )

    titulo = {
        "EN_GARANTIA": "Servidores en Garantía",
        "POR_VENCER": "Servidores por Vencer Garantía",
        "VENCIDA": "Servidores Fuera de Garantía"
    }.get(estado, "Reporte de Garantías")

    html = render_template(
        "reporte_garantias_pdf.html",
        servidores=servidores,
        titulo=titulo,
        fecha=datetime.now().strftime("%d/%m/%Y %H:%M"),
        localidad=localidad
    )

    pdf = generar_pdf(html)

    cuerpo = f"""
    <p>Buen día,</p>
    <p>Se comparte el <strong>{titulo}</strong> para la localidad <strong>{localidad}</strong>.</p>
    <p>Quedo atento a cualquier comentario.</p>
    <br>
    <p>Saludos.</p>
    """

    enviar_pdf_outlook(
        asunto=f"{titulo} - {localidad}",
        cuerpo_html=cuerpo,
        pdf_bytes=pdf,
        nombre_pdf=f"reporte_garantias_{localidad}_{estado}.pdf",
        destinatarios=destinatarios
    )

    flash("Correo preparado en Outlook", "success")
    return redirect(
        url_for("base_servidores.reporte_garantias", estado=estado, localidad=localidad)
    )

@base_servidores_bp.route("/base-servidores/garantias")
def selector_garantias():
    return render_template("reporte_garantias_selector.html")

