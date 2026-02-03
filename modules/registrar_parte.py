from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from modules.users_repository import obtener_ingenieros
from modules.utils_personal_citi import obtener_personal_citi
from db import get_connection

registrar_parte_bp = Blueprint(
    "registrar_parte_bp",
    __name__,
    template_folder="../templates",
    url_prefix="/registrar_parte"
)
LOCALIDADES_MAP = {
    "QUERETARO": "QRO",
    "TULTITLAN": "TULT"
}

# ==========================
# Utilidades
# ==========================
def normalizar(valor):
    return str(valor).strip().upper() if valor else ""

def ejecutar_query(sql, params=None, fetchone=False, fetchall=False):
    """Ejecuta un query en MySQL y devuelve resultado."""
    cnx = get_connection()
    if cnx is None:
        raise Exception("No se pudo conectar a la base de datos")
    
    cursor = cnx.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        cnx.commit()
        return result
    finally:
        cursor.close()
        cnx.close()

# ==========================
# Funciones de datos
# ==========================
def obtener_datos_caso(caso_ibm):
    """
    Trae la última parte registrada para un caso.
    Esto asegura que columnas como 'serie_equipo' existan.
    """
    sql = """
    SELECT serie_equipo, host_name, caso_citi, ubicacion, localidad, caso_proveedor
    FROM registro_partes_usadas
    WHERE caso_ibm=%s
    ORDER BY fecha DESC
    LIMIT 1
    """
    row = ejecutar_query(sql, (caso_ibm,), fetchone=True)
    return row or {}

def caso_tiene_parte_en_registro_partes(caso_ibm):
    sql = "SELECT COUNT(*) AS total FROM registro_partes_usadas WHERE caso_ibm=%s"
    row = ejecutar_query(sql, (caso_ibm,), fetchone=True)
    return row["total"] > 0 if row else False

def descontar_kit(fru, cantidad_usada, localidad):
    sql_sel = """
        SELECT cantidad, cantidad_actual
        FROM kit_partes
        WHERE fru_ibm = %s
          AND localidad = %s
        LIMIT 1
    """
    row = ejecutar_query(sql_sel, (fru, localidad), fetchone=True)

    mensaje = None

    if row:
        stock_base = row["cantidad"] or 0
        stock_actual = row["cantidad_actual"] or 0

        nuevo_stock = stock_actual - cantidad_usada

        sql_upd = """
            UPDATE kit_partes
            SET cantidad_actual = %s
            WHERE fru_ibm = %s
              AND localidad = %s
        """
        ejecutar_query(sql_upd, (nuevo_stock, fru, localidad))

        # Alerta si se va a negativo o por debajo del stock base esperado
        if nuevo_stock < 0:
            mensaje = (
                f"⚠ Stock negativo para {fru}. "
                f"Disponibles: {stock_actual}, usados: {cantidad_usada}"
            )
        elif nuevo_stock < stock_base:
            mensaje = (
                f"⚠ Stock bajo para {fru}. "
                f"Stock base: {stock_base}, disponible: {nuevo_stock}"
            )

    return mensaje

# ==========================
# Ruta principal
# ==========================
@registrar_parte_bp.route("/", methods=["GET", "POST"])
def registrar_parte():
    
    caso_ibm = request.args.get("caso_ibm")
    localidad = request.args.get("localidad") or request.form.get("localidad") or ""
    localidad = normalizar(localidad)
    localidad_mapa = LOCALIDADES_MAP.get(localidad.upper(), localidad)
    
    ingenieros = obtener_ingenieros(localidad)

    if request.method == "POST":
        # Datos del formulario
        datos = {
            "tipo_parte": request.form.get("tipo_parte"),
            "caso_ibm": request.form.get("caso_ibm"),
            "localidad": request.form.get("localidad"),
            "fecha": request.form.get("fecha") or datetime.now(),
            "marca": request.form.get("marca"),
            "parte": request.form.get("parte"),
            "descripcion": request.form.get("descripcion"),
            "modelo": request.form.get("modelo"),
            "fru_ibm": request.form.get("fru"),
            "num_proveedor": request.form.get("num_proveedor"),
            "serie_retirada": request.form.get("serie_retirada"),
            "serie_instalada": request.form.get("serie_instalada"),
            "serie_equipo": request.form.get("serie_equipo"),  # <- coincidir con template
            "host_name": request.form.get("host_name"),
            "caso_citi": request.form.get("caso_citi"),
            "caso_proveedor": request.form.get("caso_proveedor"),
            "ubicacion": request.form.get("ubicacion"),
            "ingeniero": request.form.get("ingeniero"),
            "se_entrega": request.form.get("se_entrega"),
            "cantidad": int(request.form.get("cantidad") or 1),
            "fecha_entrega": request.form.get("fecha_entrega"),
            "orden_proveedor": request.form.get("orden_proveedor"),
            "work_order": request.form.get("work_order"),
            "orden_ibm": request.form.get("orden_ibm"),
            "notas": request.form.get("notas"),
        }

        # Insertar en la tabla registro_partes_usadas
        sql_insert = """
        INSERT INTO registro_partes_usadas (
            fecha, parte, marca, modelo, numero_parte_proveedor, fru_ibm, descripcion,
            serie_retirada, serie_instalada, serie_equipo, host_name, caso_citi, caso_ibm,
            caso_proveedor, orden_proveedor, work_order, orden_ibm, ingeniero,se_entrega, cantidad,
            localidad, ubicacion, fecha_entrega, notas
        ) VALUES (
            %(fecha)s, %(parte)s, %(marca)s, %(modelo)s, %(num_proveedor)s, %(fru_ibm)s, %(descripcion)s,
            %(serie_retirada)s, %(serie_instalada)s, %(serie_equipo)s, %(host_name)s, %(caso_citi)s, %(caso_ibm)s,
            %(caso_proveedor)s, %(orden_proveedor)s, %(work_order)s, %(orden_ibm)s, %(ingeniero)s, %(se_entrega)s, %(cantidad)s,
            %(localidad)s, %(ubicacion)s, %(fecha_entrega)s, %(notas)s
        )
        """
        ejecutar_query(sql_insert, datos)
        
        if datos.get("tipo_parte") == "KIT":
            mensaje = descontar_kit(
                fru=datos.get("fru_ibm"),
                cantidad_usada=datos.get("cantidad"),
                localidad=datos.get("localidad")
            )

            if mensaje:
                flash(mensaje, "warning")

        flash("Parte registrada correctamente.", "success")
        session["preguntar_otro_registro"] = True
        return redirect(url_for("registrar_parte_bp.registrar_parte", caso_ibm=caso_ibm, localidad=localidad))

    # GET: traer datos del caso
    datos_caso = obtener_datos_caso(caso_ibm)
    print("INGENIEROS:", ingenieros)

    return render_template(
        "Registrar_Parte.html",
        caso_ibm=caso_ibm,
        localidad=localidad,
        datos_caso=datos_caso,
        ingenieros=ingenieros,
        fecha=datetime.now().strftime("%Y-%m-%dT%H:%M")
    )
    
@registrar_parte_bp.route("/get_partes/<tipo_parte>/<marca>/<localidad>")
def get_partes(tipo_parte, marca, localidad):
    tipo_parte = tipo_parte.strip().upper()
    marca = normalizar(marca)
    localidad = LOCALIDADES_MAP.get(localidad.upper(), normalizar(localidad))

    if tipo_parte == "ALMACEN":
        sql = """
            SELECT DISTINCT componente
            FROM partes_fru
            WHERE UPPER(marca) = %s
        """
        rows = ejecutar_query(sql, (marca,), fetchall=True)
        partes = [r["componente"] for r in rows]

    elif tipo_parte == "KIT":
        sql = """
            SELECT DISTINCT componente
            FROM kit_partes
            WHERE UPPER(marca) = %s
            AND UPPER(localidad) = %s
            AND cantidad > 0
        """
        rows = ejecutar_query(sql, (marca, localidad), fetchall=True)
        partes = [r["componente"] for r in rows]

    else:
        partes = []

    return jsonify(sorted(partes))

@registrar_parte_bp.route("/get_detalles/<tipo_parte>/<marca>/<parte>/<localidad>")
def get_detalles(tipo_parte, marca, parte, localidad):
    tipo_parte = tipo_parte.strip().upper()
    marca = normalizar(marca)
    parte = normalizar(parte)
    localidad = LOCALIDADES_MAP.get(localidad.upper(), normalizar(localidad))

    if tipo_parte == "ALMACEN":
        sql = """
            SELECT DISTINCT detalle
            FROM partes_fru
            WHERE UPPER(marca) = %s
              AND UPPER(componente) = %s
        """
        rows = ejecutar_query(sql, (marca, parte), fetchall=True)
        detalles = [r["detalle"] for r in rows]

    elif tipo_parte == "KIT":
        sql = """
            SELECT DISTINCT descripcion
            FROM kit_partes
            WHERE UPPER(marca) = %s
            AND UPPER(componente) = %s
            AND UPPER(localidad) = %s
            AND cantidad_actual > 0
        """
        rows = ejecutar_query(
            sql,
            (marca, parte, localidad),
            fetchall=True
        )
        detalles = [r["descripcion"] for r in rows]

    return jsonify(sorted(detalles))

@registrar_parte_bp.route("/get_info_parte")
def get_info_parte():
    
    tipo = request.args.get("tipo")
    marca = normalizar(request.args.get("marca"))
    parte = normalizar(request.args.get("parte"))
    detalle = normalizar(request.args.get("detalle"))
    localidad = normalizar(request.args.get("localidad"))
    localidad = LOCALIDADES_MAP.get(localidad.upper(), localidad)
    if tipo == "ALMACEN":
        sql = """
            SELECT fru_ibm, spare_part
            FROM partes_fru
            WHERE UPPER(marca) = %s
                AND UPPER(componente) = %s
                AND UPPER(detalle) = %s
            LIMIT 1
        """
        row = ejecutar_query(sql, (marca, parte, detalle), fetchone=True)

        if row:
            return jsonify({
                "parte_ibm": row["fru_ibm"] or "",
                "parte_proveedor": row["spare_part"] or ""
            })

        return jsonify({})

    elif tipo == "KIT":
        detalle_like = f"%{detalle}%"

        sql = """
            SELECT fru_ibm, oem_propio, cantidad_actual
            FROM kit_partes
            WHERE UPPER(marca) = %s
            AND UPPER(componente) = %s
            AND UPPER(descripcion) LIKE %s
            AND UPPER(localidad) = %s
            AND cantidad_actual > 0
            ORDER BY cantidad_actual DESC
            LIMIT 1
        """

        row = ejecutar_query(
            sql,
            (marca, parte, detalle_like, localidad),
            fetchone=True
        )

        if row:
            return jsonify({
                "parte_ibm": row["fru_ibm"] or "",
                "parte_proveedor": row["oem_propio"] or "",
                "stock": row["cantidad_actual"] or 0
            })

        return jsonify({})


@registrar_parte_bp.route("/get_stock_kit/<localidad>/<marca>/<fru>")
def get_stock_kit(localidad, marca, fru):

    sql = """
        SELECT
            cantidad AS cantidad_total,
            cantidad_actual AS disponible
        FROM kit_partes
        WHERE UPPER(localidad) = %s
          AND UPPER(marca) = %s
          AND UPPER(fru_ibm) = %s
        LIMIT 1
    """
    localidad_mapa = LOCALIDADES_MAP.get(normalizar(localidad).upper(), normalizar(localidad))
    row = ejecutar_query(
        sql,
        (localidad_mapa, normalizar(marca), fru.strip().upper()),
        fetchone=True
    )

    return jsonify(row or {"cantidad_total": 0, "disponible": 0})

@registrar_parte_bp.route("/get_personal_citi/<localidad>")
def get_personal_citi(localidad):
    
    localidad_mapa = LOCALIDADES_MAP.get(localidad.upper(), localidad)
    personal = obtener_personal_citi(localidad)

    return jsonify(personal)

@registrar_parte_bp.route("/get_info_parte_almacen")
def get_info_parte_almacen():
    marca = normalizar(request.args.get("marca", ""))
    parte = normalizar(request.args.get("parte", ""))
    detalle = normalizar(request.args.get("detalle", ""))
    localidad = normalizar(request.args.get("localidad", ""))

    sql = """
        SELECT fru_ibm, spare_part
        FROM partes_fru
        WHERE UPPER(marca) = %s
          AND UPPER(componente) = %s
          AND UPPER(detalle) = %s
        LIMIT 1
    """
    row = ejecutar_query(
        sql,
        (marca, parte, detalle),
        fetchone=True
    )

    if row:
        return jsonify({
            "parte_ibm": row["fru_ibm"] or "",
            "parte_proveedor": row["spare_part"] or ""
        })

    return jsonify({})

@registrar_parte_bp.route("/get_datos_caso/<caso_ibm>")
def get_datos_caso(caso_ibm):
    sql = """
        SELECT
            serie,
            hostname,
            caso_citi,
            ingeniero,
            alciti,
            ubicacion_parte
        FROM casos
        WHERE caso_ibm = %s
        LIMIT 1
    """
    row = ejecutar_query(sql, (caso_ibm,), fetchone=True)

    if row:
        return jsonify({
            "serie_equipo": row["serie"] or "",
            "host_name": row["hostname"] or "",
            "caso_citi": row["caso_citi"] or "",
            "ingeniero_ibm": row["ingeniero"] or "",
            "ubicacion": row["ubicacion_parte"] or "",
            "ingeniero_citi": row["alciti"] or ""
        })

    return jsonify({})