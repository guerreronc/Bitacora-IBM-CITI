# modules/casos_routes.py
from flask import Blueprint, render_template, request, redirect, jsonify, session, url_for,flash
import os
from datetime import datetime as _dt
from db import get_connection
from helpers.utils_tiempos import recalcular_tiempos_mysql, to_dt_mysql
from modules.users_repository import obtener_ingenieros
from modules.casos_repository import listar_casos
#from modules.casos_repository import caso_tiene_parte_en_registro_partes

casos_bp = Blueprint("casos", __name__)

def caso_tiene_parte_registrada_mysql(caso_ibm):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 1
        FROM registro_partes_usadas
        WHERE caso_ibm = %s
        LIMIT 1
    """, (caso_ibm,))

    existe = cur.fetchone() is not None

    cur.close()
    conn.close()

    return existe

# ============================
# LISTAR CASOS
# ============================
@casos_bp.route("/casos")
def casos():
    localidad = request.args.get("localidad", "").strip().upper()
    id_caso = request.args.get("id_caso", "").strip()
    filtro = request.args.get("filtro", "").strip().lower()

    casos_list = listar_casos(
        localidad=localidad or None,
        id_caso=id_caso or None,
        filtro=filtro or None
    )

    return render_template(
        "Casos.html",
        casos=casos_list,
        sucursal=localidad,
        filtro_localidad=localidad,
        user=session.get("user")
    )
    
# ============================
# EDITAR CASO (GET)
# ============================
@casos_bp.route("/editar_caso/<id_caso>")
def editar_caso(id_caso):
    # -------------------------
    # Obtener conexión y cursor
    # -------------------------
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    

    # -------------------------
    # Traer registro del caso
    # -------------------------
    query = """
        SELECT *
        FROM casos
        WHERE caso_ibm = %s
    """
    cursor.execute(query, (id_caso,))
    caso_encontrado = cursor.fetchone()
    cursor.close()
    conn.close()

    if not caso_encontrado:
        return "Caso no encontrado", 404
    # -------------------------
    # Convertir fechas a string para HTML
    # -------------------------
    
        # Campo FECHA -> dd-mm-yyyy HH:mm
    caso_encontrado["fecha"] = _dt.now().strftime("%Y-%m-%d %H:%M")
        
    campos_fecha = [
        "fecha_apertura",
        "fecha_garantia",
        "fecha_alerta",
        "fecha_solucion",
        "inicio_analisis",
        "fin_analisis",
        "inicio_atencion",
        "fin_atencion",
        "ventana"
    ]    
    for f in campos_fecha:
        valor = caso_encontrado.get(f)
        if valor:
            # Si es datetime, convertir a string "YYYY-MM-DDTHH:MM" para input type=datetime-local
            if isinstance(valor, _dt):
                caso_encontrado[f] = valor.strftime("%Y-%m-%dT%H:%M")
            else:
                # Si ya es string, intentar normalizarlo o dejarlo igual
                caso_encontrado[f] = valor
        else:
            caso_encontrado[f] = ""

    # -------------------------
    # Verificar si ya hay parte registrada
    # -------------------------
    #parte_registrada = caso_tiene_parte_en_registro_partes(id_caso)
    
    parte_registrada = caso_tiene_parte_registrada_mysql(id_caso)
    # -------------------------
    # Mapear MySQL -> HTML (cla ves que usa template)
    # -------------------------
    caso = {
        "FECHA": caso_encontrado["fecha"],
        "CASO IBM": caso_encontrado["caso_ibm"],
        "CASO CITI": caso_encontrado["caso_citi"],
        "ALCITI": caso_encontrado.get("alciti"),
        "SEGUIMIENTO CITI": caso_encontrado.get("seguimiento"),
        "INGENIERO": caso_encontrado["ingeniero"],
        "SERIE EQUIPO": caso_encontrado["serie"],
        "HOST NAME": caso_encontrado["hostname"],
        "STATUS": caso_encontrado["status"],
        "FALLA": caso_encontrado["falla"],
        "CASO PROOVEDOR": caso_encontrado.get("caso_proveedor"),
        "UBICACION": caso_encontrado.get("ubicacion"),
        "MARCA": caso_encontrado.get("marca"),
        "MODELO": caso_encontrado.get("modelo"),
        "MARCA CSP": caso_encontrado.get("marca_csp"),
        "MODELO CSP": caso_encontrado.get("modelo_csp"),
        "STATUS PRINCIPAL": caso_encontrado["status_principal"],
        "FECHA DE APERTURA": caso_encontrado.get("fecha_apertura"),
        "FECHA GARANTIA": caso_encontrado.get("fecha_garantia"),
        "FECHA ALERTAMIENTO": caso_encontrado.get("fecha_alerta"),
        "FECHA SOLUCION": caso_encontrado.get("fecha_solucion"),
        "INICIO DE ATENCION": caso_encontrado.get("inicio_atencion"),
        "FIN DE ATENCION": caso_encontrado.get("fin_atencion"),
        "FECHA INICIO ANALISIS": caso_encontrado.get("inicio_analisis"),
        "FECHA FIN ANALISIS": caso_encontrado.get("fin_analisis"),
        "VENTANA DE SERVICIO": caso_encontrado.get("ventana"),
        "SE NECESITA PARTE": caso_encontrado.get("needpart"),
        "UBICACIÓN DE PARTE": caso_encontrado.get("ubicacion_parte"),
        "NOTAS": caso_encontrado.get("notas"),
        "LOCALIDAD": caso_encontrado.get("localidad"),
        "VOBO SITIO": caso_encontrado.get("vobo_sitio"),
        "VOBO CLIENTE": caso_encontrado.get("vobo_cliente"),
    }

    # -------------------------
    # Listas dinámicas para selects
    # -------------------------
    localidad = (caso_encontrado.get("localidad") or "").upper()
    localidades = [localidad]

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

    if localidad == "QUERETARO":
        seguimiento_citi = seguimiento_citi_qro
    elif localidad == "TULTITLAN":
        seguimiento_citi = seguimiento_citi_tult
    else:
        seguimiento_citi = []

    severidades = ["BAJA", "MEDIA", "ALTA", "CRITICA"]
    fallas = ["HDD","DIMM","SYSTEM BOARD","POWER SUPPLY","FAN","NIC CARD","POWER DRAIN","SURVEY/CONFIGURACION","SISTEMA/ILO/IDRAC"]
    status_opts = ["ABIERTO","CERRADO","PENDIENTE LOGS","PENDIENTE CLIENTE","PENDIENTE PARTE","PENDIENTE VALIDACION","PENDIENTE VENTANA","PROGRAMADO"]
    tipo_servicio = ["BREAK AND FIX","HRS IMAX"]

    # -------------------------
    # Ingenieros disponibles según localidad
    # -------------------------
    ingenieros_disponibles = obtener_ingenieros(localidad)

    # -------------------------
    # Render template
    # -------------------------
    return render_template(
        "Editar_Caso.html",
        caso=caso,
        parte_registrada=parte_registrada,
        localidades=localidades,
        severidades=severidades,
        fallas=fallas,
        status_opts=status_opts,
        tipo_servicio=tipo_servicio,
        ingenieros_disponibles=ingenieros_disponibles,
        seguimiento_citi=seguimiento_citi,
        user=session.get("user")
    )

# ============================
# GUARDAR EDICIÓN (POST) - MySQL
# ============================
@casos_bp.route("/guardar_edicion/<caso_ibm>", methods=["POST"])
def guardar_edicion(caso_ibm):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        f = request.form
        accion = f.get("accion", "guardar")

        # -------------------------
        # Convertir fechas
        # -------------------------
        fechas = {
            "fecha": to_dt_mysql(f.get("FECHA")),
            "fecha_apertura": to_dt_mysql(f.get("FECHA DE APERTURA")),
            "fecha_alerta": to_dt_mysql(f.get("FECHA ALERTAMIENTO")),
            "fecha_solucion": to_dt_mysql(f.get("FECHA SOLUCION")),
            "inicio_analisis": to_dt_mysql(f.get("FECHA INICIO ANALISIS")),
            "fin_analisis": to_dt_mysql(f.get("FECHA FIN ANALISIS")),
            "inicio_atencion": to_dt_mysql(f.get("INICIO DE ATENCION")),
            "fin_atencion": to_dt_mysql(f.get("FIN DE ATENCION")),
            "fecha_garantia": to_dt_mysql(f.get("FECHA GARANTIA")),
        }
        # -------------------------
        # Validaciones de cierre
        # -------------------------
        if accion == "cerrar":

            # Validar VOBO CLIENTE
            if not f.get("VOBO CLIENTE"):
                flash("No se puede cerrar el caso sin VOBO del cliente", "warning")
                return redirect(url_for("casos.editar_caso", id_caso=caso_ibm))

            # Validar VOBO SITIO
            if not f.get("VOBO SITIO"):
                flash("No se puede cerrar el caso sin VOBO en sitio", "warning")
                return redirect(url_for("casos.editar_caso", id_caso=caso_ibm))

            # Validar partes si needpart = SI
            if f.get("SE NECESITA PARTE") == "SI":
                if not caso_tiene_parte_registrada_mysql(caso_ibm):
                    flash("Debe registrar la parte antes de cerrar el caso", "warning")
                    return redirect(url_for("casos.editar_caso", id_caso=caso_ibm))

            # Forzar cierre
            f = f.copy()
            f = dict(f)
            f["STATUS"] = "CERRADO"
            f["STATUS PRINCIPAL"] = "CERRADO"

        # -------------------------
        # UPDATE MySQL
        # -------------------------
        sql = """
        UPDATE casos
        SET
            fecha = %(fecha)s,
            alciti = %(alciti)s,
            seguimiento = %(seguimiento)s,
            caso_citi = %(caso_citi)s,
            fecha_apertura = %(fecha_apertura)s,
            severidad = %(severidad)s,
            ingeniero = %(ingeniero)s,
            serie = %(serie)s,
            hostname = %(hostname)s,
            ubicacion = %(ubicacion)s,
            marca = %(marca)s,
            modelo = %(modelo)s,
            fecha_garantia = %(fecha_garantia)s,
            caso_proveedor = %(caso_proveedor)s,
            falla = %(falla)s,
            ventana = %(ventana)s,
            status = %(status)s,
            tipo_servicio = %(tipo_servicio)s,
            needpart = %(needpart)s,
            ubicacion_parte = %(ubicacion_parte)s,
            notas = %(notas)s,
            status_principal = %(status_principal)s,
            marca_csp = %(marca_csp)s,
            modelo_csp = %(modelo_csp)s,
            fecha_alerta = %(fecha_alerta)s,
            fecha_solucion = %(fecha_solucion)s,
            inicio_analisis = %(inicio_analisis)s,
            fin_analisis = %(fin_analisis)s,
            inicio_atencion = %(inicio_atencion)s,
            fin_atencion = %(fin_atencion)s,
            localidad = %(localidad)s,
            vobo_sitio = %(vobo_sitio)s,
            vobo_cliente = %(vobo_cliente)s
        WHERE caso_ibm = %(caso_ibm)s
        """

        params = {
            **fechas,
            "alciti": f.get("ALCITI"),
            "seguimiento": f.get("SEGUIMIENTO CITI"),
            "caso_citi": f.get("CASO CITI"),
            "severidad": f.get("SEVERIDAD"),
            "ingeniero": f.get("INGENIERO"),
            "serie": f.get("SERIE EQUIPO"),
            "hostname": f.get("HOST NAME"),
            "ubicacion": f.get("UBICACION"),
            "marca": f.get("MARCA"),
            "modelo": f.get("MODELO"),
            "caso_proveedor": f.get("CASO PROOVEDOR"),
            "falla": f.get("FALLA"),
            "ventana": f.get("VENTANA DE SERVICIO"),
            "status": f.get("STATUS"),
            "status_principal": f.get("STATUS PRINCIPAL"),
            "tipo_servicio": f.get("TIPO DE SERVICIO"),
            "needpart": f.get("SE NECESITA PARTE"),
            "ubicacion_parte": f.get("UBICACIÓN DE PARTE"),
            "notas": f.get("NOTAS"),
            "marca_csp": f.get("MARCA CSP"),
            "modelo_csp": f.get("MODELO CSP"),
            "localidad": f.get("LOCALIDAD"),
            "vobo_sitio": f.get("VOBO SITIO"),
            "vobo_cliente": f.get("VOBO CLIENTE"),
            "caso_ibm": caso_ibm,
        }

        cur.execute(sql, params)
        conn.commit()

        recalcular_tiempos_mysql(cur, caso_ibm)
        conn.commit()
        
        flash("Cambios guardados correctamente", "success")
        return redirect(url_for("casos.editar_caso", id_caso=caso_ibm))

    except Exception as e:
        conn.rollback()
        flash(f"Error al guardar: {e}", "danger")
        return redirect(url_for("casos.editar_caso", id_caso=caso_ibm))

# ============================
# OTRAS RUTAS AUXILIARES
# ============================
@casos_bp.route("/get_ingenieros")
def get_ingenieros():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT nombre
        FROM usuarios
        WHERE rol IN ('engineer', 'admin')
          AND activo = 1
        ORDER BY nombre
    """)

    ingenieros = [row["nombre"] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return jsonify(ingenieros)

#-------------------------
# CERRAR CASO 
#-------------------------
@casos_bp.route("/cerrar-caso/<caso_id>", methods=["POST"])
def cerrar_caso(caso_id):

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Obtener datos críticos del caso
    cur.execute("""
        SELECT
            status,
            status_principal,
            needpart,
            vobo_sitio,
            vobo_cliente
        FROM casos
        WHERE caso_ibm = %s
    """, (caso_id,))

    caso = cur.fetchone()

    if not caso:
        flash("Caso no encontrado", "danger")
        return redirect(url_for("casos.casos"))

    # 1️⃣ Validar VOBO CLIENTE
    if not caso["vobo_cliente"] or caso["vobo_cliente"].strip() == "":
        flash("No se puede cerrar el caso: falta el VOBO del cliente", "warning")
        return redirect(url_for("casos.editar_caso", id_caso=caso_id))

    # 2️⃣ Validar VOBO SITIO
    if not caso["vobo_sitio"] or caso["vobo_sitio"].strip() == "":
        flash("No se puede cerrar el caso: falta el VOBO en sitio", "warning")
        return redirect(url_for("casos.editar_caso", id_caso=caso_id))

    # 3️⃣ Validar parte si needpart = SI
    if caso["needpart"] == "SI":
        if not caso_tiene_parte_registrada_mysql(caso_id):
            flash(
                "No se puede cerrar el caso: se requiere registrar al menos una parte",
                "warning"
            )
            return redirect(url_for("casos.editar_caso", id_caso=caso_id))

    # 4️⃣ Cerrar caso
    cur.execute("""
        UPDATE casos
        SET
            status = 'CERRADO',
            status_principal = 'CERRADO'
        WHERE caso_ibm = %s
    """, (caso_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("CASO CERRADO CORRECTAMENTE", "success")
    return redirect(url_for("casos.editar_caso", id_caso=caso_id))
#--------------------------------
# ELIMINAR CASO SOLO PARA ADMIN
#--------------------------------
@casos_bp.route("/casos/eliminar/<caso_ibm>", methods=["POST"])
def eliminar_caso(caso_ibm):
    user = session.get("user")
    if not user or user.get("role") != "ADMIN":
        return jsonify({"error": "No autorizado"}), 403

    # Opcional: prevenir eliminación si ya tiene partes registradas
    if caso_tiene_parte_registrada_mysql(caso_ibm):
        return jsonify({"error": "No se puede eliminar: hay partes registradas"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM casos WHERE caso_ibm = %s", (caso_ibm,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True})

#----------------------------
# REABRIR CASO SOLO POR ADMIN
#----------------------------
@casos_bp.route("/reabrir/<caso_ibm>", methods=["POST"])
def reabrir_caso(caso_ibm):
    user = session.get("user")
    if not user or user.get("role", "").upper() != "ADMIN":
        return jsonify({"error": "No autorizado"}), 403

    conn = get_connection()
    cursor = conn.cursor()

    # Solo reabrir si estaba cerrado
    cursor.execute("SELECT status, status_principal FROM casos WHERE caso_ibm = %s", (caso_ibm,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Caso no encontrado"}), 404

    status, status_principal = row
    if (status or "").upper() != "CERRADO" and (status_principal or "").upper() != "CERRADO":
        cursor.close()
        conn.close()
        return jsonify({"error": "El caso no está cerrado"}), 400

    # Actualizamos ambos campos a ABIERTO (o el valor que corresponda)
    cursor.execute("""
        UPDATE casos
        SET status = 'ABIERTO', status_principal = 'ABIERTO'
        WHERE caso_ibm = %s
    """, (caso_ibm,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})


