# modules/crear_caso.py
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash,session
from modules.users_repository import obtener_ingenieros
from db import get_connection

# -----------------------
# Helpers
# -----------------------
def _parse_dt(v):
    """Convierte string datetime-local / string común / date / datetime a datetime o None."""
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    try:
        # datetime-local: YYYY-MM-DDTHH:MM
        return datetime.fromisoformat(v)
    except Exception:
        try:
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                return datetime.strptime(v, "%Y-%m-%d")
            except Exception:
                return None


def _set_cell(ws, r, c, value):
    """Escribe None o value sin lógica adicional."""
    ws.cell(row=r, column=c).value = value if value not in ("", None) else None


def _next_empty_row(ws, start_row=2, col=1):
    r = start_row
    while ws.cell(row=r, column=col).value is not None:
        r += 1
    return r


# -----------------------
# Registro del módulo
# -----------------------
def register_crear_caso(app):

    @app.route("/crear_caso", methods=["GET", "POST"])
    def crear_caso():
        # -----------------------
        # Listas fijas (UI)
        # -----------------------
        seguimiento_citi_qro = [
            "ALVARADO LEON CARINA LUZ",
            "CARRERA HERNANDEZ ERNESTO MICHELLE",
            "ARGUELLO CASTRO LUIS GUILLERMO",
            "MARTINEZ FRANCISCO JAVIER",
            "RAMIREZ OSCAR ALBERTO",
            "WALKTROUGHT",
        ]
        seguimiento_citi_tult = [
            "BERENICE PIEDAD FLORESZ",
            "POLETH JIMENEZ GONZALEZ",
            "DANIEL MORALES",
            "ERICK L. LUCIANNO",
            "JAVIER REYES NAVARRETE",
            "WALKTROUGHT",
        ]
        severidades = ["1 ALTA", "2 MEDIA", "3 BAJA", "4 MUY BAJA"]
        
        localidad = session.get("localidad", "QUERETARO")
        ingenieros = obtener_ingenieros(localidad)

    
        fallas = [
            "HDD",
            "DIMM",
            "SYSTEM BOARD",
            "POWER SUPPLY",
            "FAN",
            "NIC CARD",
            "POWER DRAIN",
            "SISTEMA/ILO/IDRAC",
            "SURVEY/CONFIGURACION",
        ]
        status_list = [
            "ABIERTO",
            "PENDIENTE LOGS",
            "PENDIENTE CLIENTE",
            "PENDIENTE PARTE",
            "PENDIENTE VALIDACION",
            "PENDIENTE VENTANA",
            "PROGRAMADO",
            "CERRADO",
        ]
        status_principal = ["ABIERTO", "CERRADO"]
        tipos_servicio = ["BREAK AND FIX", "HRS IMAX"]
        needpart_options = ["SI", "NO"]

        # -----------------------
        # Series dinámicas por LOCALIDAD (MySQL - base_servers)
        # -----------------------
        series_list = []

        localidad = session.get("localidad", "QUERETARO")

        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT serie
                    FROM base_servers
                    WHERE localidad = %s
                    ORDER BY serie
                    """,
                    (localidad,)
                )
                rows = cursor.fetchall()
                series_list = [row[0] for row in rows if row[0]]

            except Exception as e:
                print("Error cargando series desde MySQL:", e)

            finally:
                cursor.close()
                conn.close()

        # -----------------------
        # POST: Guardar Caso
        # -----------------------
        if request.method == "POST":
            form = request.form

            # Fechas
            fecha = _parse_dt(form.get("fecha"))
            fecha_alerta = _parse_dt(form.get("fecha_alerta"))
            fecha_apertura = _parse_dt(form.get("fecha_apertura"))
            fecha_solucion = _parse_dt(form.get("fecha_solucion"))
            inicio_analisis = _parse_dt(form.get("inicio_analisis"))
            fin_analisis = _parse_dt(form.get("fin_analisis"))
            inicio_atencion = _parse_dt(form.get("inicio_atencion"))
            fin_atencion = _parse_dt(form.get("fin_atencion"))

            # Campos directos
            alciti = form.get("alciti")
            seguimiento = form.get("seguimiento_citi")
            caso_ibm = form.get("caso_ibm")
            caso_citi = form.get("caso_citi")
            severidad = form.get("severidad")
            ingeniero = form.get("ingeniero")

            serie = form.get("serie_equipo") or form.get("txt_serie") or ""
            txt_serie = form.get("txt_serie") or serie
            nombre_server = form.get("nombre_server")
            ubicacion = form.get("ubicacion")
            proveedor = form.get("proveedor")
            modelo = form.get("text_modelo")
            marca_csp = form.get("marca_csp")
            modelo_csp = form.get("modelo_csp")
            fecha_garantia = form.get("fecha_garantia")
            caso_proveedor = form.get("caso_proveedor")

            falla_reportada = form.get("falla_reportada")
            ventana_servicio = form.get("ventana_servicio")
            status = form.get("status")
            status_principal_val = form.get("status_principal")
            tipo_servicio = form.get("tipo_servicio")
            needpart = form.get("needpart")
            ubicacion_parte = form.get("ubicacion_parte")
            notas = form.get("notas")
            localidad = form.get("localidad")

            # Fecha garantía (string -> datetime si aplica)
            fecha_garantia = _parse_dt(form.get("fecha_garantia"))

            # -----------------------
            # Guardar en MySQL
            # -----------------------
            try:
                conn = get_connection()
                cursor = conn.cursor()

                sql = """
                INSERT INTO casos (
                    fecha, alciti, seguimiento, caso_ibm, caso_citi, fecha_apertura,
                    severidad, ingeniero, serie, hostname, ubicacion, marca, modelo,
                    fecha_garantia, caso_proveedor, falla, ventana, status, tipo_servicio,
                    needpart, ubicacion_parte, notas, status_principal, marca_csp, modelo_csp,
                    fecha_alerta, fecha_solucion, inicio_analisis, fin_analisis,
                    inicio_atencion, fin_atencion,
                    tiempo_apertura, tiempo_analisis, tiempo_atencion, tiempo_reporte,
                    localidad
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s,%s,
                    %s,%s,%s,%s,
                    %s
                )
                """

                values = (
                    fecha,
                    alciti,
                    seguimiento,
                    caso_ibm,
                    caso_citi,
                    fecha_apertura,
                    severidad,
                    ingeniero,
                    txt_serie,
                    nombre_server,
                    ubicacion,
                    proveedor,
                    modelo,
                    fecha_garantia,
                    caso_proveedor,
                    falla_reportada,
                    ventana_servicio,
                    status,
                    tipo_servicio,
                    needpart,
                    ubicacion_parte,
                    notas,
                    status_principal_val,
                    marca_csp,
                    modelo_csp,
                    fecha_alerta,
                    fecha_solucion,
                    inicio_analisis,
                    fin_analisis,
                    inicio_atencion,
                    fin_atencion,
                    None,  # tiempo_apertura
                    None,  # tiempo_analisis
                    None,  # tiempo_atencion
                    None,  # tiempo_reporte
                    localidad
                )

                cursor.execute(sql, values)
                conn.commit()

                flash("Caso {caso_ibm} registrado correctamente en MySQL.", "success")
                return redirect(url_for("crear_caso"))

            except Exception as e:
                print("Error guardando en MySQL:", e)
                flash(f"Error al guardar el caso: {e}", "danger")
                return redirect(url_for("crear_caso"))

            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()


        # -----------------------
        # GET: Mostrar formulario
        # -----------------------
        return render_template(
            "Crear_Caso.html",
            seguimiento_citi_qro=seguimiento_citi_qro,
            seguimiento_citi_tult=seguimiento_citi_tult,
            severidades=severidades,
            ingenieros=ingenieros,
            fallas=fallas,
            status_list=status_list,
            status_principal=status_principal,
            tipos_servicio=tipos_servicio,
            needpart_options=needpart_options,
            series_list=series_list,
        )
