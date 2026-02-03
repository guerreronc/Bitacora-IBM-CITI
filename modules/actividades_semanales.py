from flask import Blueprint, redirect, render_template, request, flash, url_for
from datetime import datetime
import smtplib
import pythoncom
import win32com.client as win32
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from db import get_connection


import os

actividades_bp = Blueprint(
    "actividades",
    __name__,
    template_folder="../templates"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_CASOS = os.path.join(BASE_DIR, "data", "BITACORA_GENERALIBMCITI.xlsx")

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USER = "tu_correo@empresa.com"
SMTP_PASSWORD = "TU_PASSWORD"

DESTINATARIOS_POR_LOCALIDAD = {
    "QUERETARO": [
        "ibm_qrcs_engineering-dg@ibm.com",
        "fvargas@mx1.ibm.com",
        "saguilar@mx1.ibm.com",
        "garcizam@mx1.ibm.com",
        "agomsan@mx1.ibm.com"
    ],
    "TULTITLAN": [
        "tultitlan1@empresa.com",
        "tultitlan2@empresa.com"
    ]
}

def buscar_casos(fecha_ini, fecha_fin, localidad):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            fecha_apertura,
            caso_ibm,
            caso_citi,
            hostname,
            serie,
            falla,
            status,
            notas,
            localidad
        FROM casos
        WHERE UPPER(localidad) = %s
          AND (
                fecha_apertura BETWEEN %s AND %s
                OR UPPER(status) <> 'CERRADO'
          )
        ORDER BY fecha_apertura ASC
    """

    cursor.execute(sql, (
        localidad.upper(),
        fecha_ini,
        fecha_fin
    ))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    resultados = []

    for r in rows:
        fecha_db = r.get("fecha_apertura")

        if not fecha_db:
            # Caso sin fecha: se omite (equivalente a Excel)
            continue

        resultados.append({
            "fecha": fecha_db.strftime("%d/%m/%Y"),
            "caso_ibm": r.get("caso_ibm"),
            "caso_citi": r.get("caso_citi"),
            "hostname": r.get("hostname"),
            "serie": r.get("serie"),
            "falla": r.get("falla"),
            "status": (r.get("status") or "").strip().upper(),
            "notas": r.get("notas", "")
        })


    return resultados

def buscar_actividades(fecha_ini, fecha_fin, localidad):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            fecha,
            registro,
            realizada_por,
            tipo,
            localidad
        FROM actividades_semanales
        WHERE fecha BETWEEN %s AND %s
          AND UPPER(localidad) = %s
        ORDER BY fecha ASC
    """

    cursor.execute(sql, (
        fecha_ini.date(),
        fecha_fin.date(),
        localidad.upper()
    ))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    actividades = []

    for r in rows:
        actividades.append({
            "fecha": r["fecha"].strftime("%d/%m/%Y"),
            "registro": r["registro"],
            "realizada_por": r["realizada_por"],
            "tipo": r["tipo"],
            "localidad": r["localidad"]
        })

    return actividades

def construir_html_reporte(casos, actividades, fecha_inicio, fecha_fin, localidad):

    LOGO_BASE64 = ""  # ← aquí puedes pegar el base64 real del logo si lo deseas

    html = f"""
    <html>
    <body style="font-family:Segoe UI, Arial, sans-serif; font-size:12px; color:#000000;">

      <!-- ENCABEZADO -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="vertical-align:middle;">
            <h2 style="color:#003366; margin-bottom:5px;">Reporte Semanal</h2>
            <p style="margin:2px 0;"><strong>Localidad:</strong> {localidad}</p>
            <p style="margin:2px 0;"><strong>Periodo:</strong> {fecha_inicio} al {fecha_fin}</p>
          </td>
          <td align="right">
            {"<img src='data:image/png;base64," + LOGO_BASE64 + "' height='50'>" if LOGO_BASE64 else ""}
          </td>
        </tr>
      </table>

      <hr style="border:0; border-top:1px solid #D0D7DE; margin:15px 0;">
    """

    # =========================
    # TABLA DE CASOS
    # =========================
    if casos:
        html += """
        <h3 style="color:#003366;">Casos</h3>

        <table width="100%" cellpadding="6" cellspacing="0"
               style="border-collapse:collapse; font-size:12px;">
          <tr>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Fecha</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">CASO IBM</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">CASO CITI</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Hostname</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Serie</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Falla</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Status</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Notas</th>
          </tr>
        """

        for i, c in enumerate(casos):
            bg = "#F4F8FC" if i % 2 == 0 else "#FFFFFF"
            html += f"""
            <tr style="background-color:{bg};">
              <td style="border:1px solid #D0D7DE;">{c['fecha']}</td>
              <td style="border:1px solid #D0D7DE;">{c['caso_ibm']}</td>
              <td style="border:1px solid #D0D7DE;">{c['caso_citi']}</td>
              <td style="border:1px solid #D0D7DE;">{c['hostname']}</td>
              <td style="border:1px solid #D0D7DE;">{c['serie']}</td>
              <td style="border:1px solid #D0D7DE;">{c['falla']}</td>
              <td style="border:1px solid #D0D7DE;">{c['status']}</td>
              <td style="border:1px solid #D0D7DE;">{c.get('notas','')}</td>
            </tr>
            """

        html += "</table><br>"

    # =========================
    # TABLA DE ACTIVIDADES
    # =========================
    if actividades:
        html += """
        <h3 style="color:#003366;">Actividades Semanales</h3>
        <h2 style="color:#003366;">Se envian las actividades que se tuvieron durante la semana</h2>
        <table width="100%" cellpadding="6" cellspacing="0"
               style="border-collapse:collapse; font-size:12px;">
          <tr>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Fecha</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Registro</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Realizada por</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Tipo</th>
            <th style="background:#003366;color:#FFFFFF;border:1px solid #D0D7DE;">Localidad</th>
          </tr>
        """

        for i, a in enumerate(actividades):
            bg = "#F4F8FC" if i % 2 == 0 else "#FFFFFF"
            html += f"""
            <tr style="background-color:{bg};">
              <td style="border:1px solid #D0D7DE;">{a['fecha']}</td>
              <td style="border:1px solid #D0D7DE;">{a['registro']}</td>
              <td style="border:1px solid #D0D7DE;">{a['realizada_por']}</td>
              <td style="border:1px solid #D0D7DE;">{a['tipo']}</td>
              <td style="border:1px solid #D0D7DE;">{a['localidad']}</td>
            </tr>
            """

        html += "</table>"

    # =========================
    # FOOTER
    # =========================
    html += """
      <hr style="border:0; border-top:1px solid #D0D7DE; margin:20px 0;">
      <p style="font-size:11px; color:#555555;">
        Envio de reportes y actividades durante la semana.
      </p>
    </body>
    </html>
    """

    return html


def abrir_correo_outlook(asunto, html, destinatarios):
    pythoncom.CoInitialize()  # ✅ INICIALIZA COM

    try:
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)

        mail.Subject = asunto
        mail.HTMLBody = html
        mail.To = "; ".join(destinatarios)

        mail.Display()  # 🔹 ABRE el correo, NO lo envía

    finally:
        pythoncom.CoUninitialize()  # ✅ CIERRA COM


@actividades_bp.route("/", methods=["GET"])
@actividades_bp.route("", methods=["GET"])
def index():
    resultados_casos = []
    resultados_actividades = []


    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    localidad = request.args.get("localidad")

    if fecha_inicio and fecha_fin and localidad:
        try:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )

        except ValueError:
            flash("Formato de fechas inválido", "danger")
            return render_template("Actividades_Semanales.html")

        resultados_casos = buscar_casos(fi, ff, localidad)
        resultados_actividades = buscar_actividades(fi, ff, localidad)

        flash(f"{len(resultados_actividades)} actividad(es) encontradas.", "success")

        if not resultados_casos:
            flash("No se encontraron casos en ese rango de fechas.", "info")
            
        flash(f"{len(resultados_casos)} caso(s) encontrados.", "success")
    mostrar_boton_envio = False

    if resultados_casos or resultados_actividades:
        mostrar_boton_envio = True

    return render_template(
        "Actividades_Semanales.html",
        resultados_casos=resultados_casos,
        resultados_actividades=resultados_actividades,
        mostrar_boton_envio=mostrar_boton_envio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        localidad=localidad
    )

@actividades_bp.route("/enviar_reporte", methods=["POST"])
def enviar_reporte():
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")
    localidad = request.form.get("localidad")

    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
    except ValueError:
        flash("Fechas inválidas.", "danger")
        return redirect(url_for("actividades.index"))

    casos = buscar_casos(fi, ff, localidad)
    actividades = buscar_actividades(fi, ff, localidad)

    if not casos and not actividades:
        flash("No hay información para enviar.", "warning")
        return redirect(url_for("actividades.index"))

    html = construir_html_reporte(
        casos,
        actividades,
        fecha_inicio,
        fecha_fin,
        localidad
    )
    destinatarios = DESTINATARIOS_POR_LOCALIDAD.get(localidad.upper())

    if not destinatarios:
        flash("No hay destinatarios configurados para esa localidad.", "danger")
        return redirect(url_for("actividades.index"))

    asunto = f"Reporte Semanal {localidad} ({fecha_inicio} al {fecha_fin})"

    abrir_correo_outlook(asunto, html, destinatarios)

    flash("Reporte semanal enviado correctamente.", "success")

    return redirect(url_for(
        "actividades.index",
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        localidad=localidad
    ))

@actividades_bp.route("/registrar", methods=["POST"])
def registrar_actividad():
    fecha = request.form.get("fecha")
    actividad = request.form.get("actividad")
    responsable = request.form.get("responsable")
    tipo = request.form.get("tipo")
    localidad = request.form.get("localidad")
    notas = request.form.get("notas")

    if not fecha or not actividad or not responsable or not tipo:
        flash("Todos los campos obligatorios deben llenarse.", "danger")
        return render_template("Actividades_Semanales.html")

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        flash("Fecha inválida.", "danger")
        return render_template("Actividades_Semanales.html")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Construir REGISTRO
        registro = actividad.strip()
        if notas:
            registro += f" | {notas.strip()}"

        sql = """
            INSERT INTO actividades_semanales
            (fecha, registro, realizada_por, tipo, localidad)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            fecha_dt.date(),
            registro,
            responsable,
            tipo,
            localidad
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Actividad semanal registrada correctamente.", "success")

    except Exception as e:
        flash(f"Error al guardar la actividad: {e}", "danger")

    return render_template("Actividades_Semanales.html")

