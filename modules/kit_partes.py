
from flask import Blueprint, abort, jsonify, render_template, request, send_file, session, redirect, url_for, flash
from datetime import datetime
import os
from db import get_connection
from helpers.utils_correo import guardar_reporte_inventario_eml
from helpers.utils_inventario import obtener_mensajes_stock_bajo
from helpers.utils_inventario import (
    obtener_partes_inventario,
    calcular_resumen_inventario
)
from helpers.utils_pdf import generar_pdf_inventario

kit_bp = Blueprint("kit_bp", __name__)

MAP_LOCALIDAD = {
    "QUERETARO": "QRO",
    "QRO": "QRO",
    "TULTITLAN": "TULT",
    "TULT": "TULT"
}

DESTINATARIOS_INVENTARIO = {
    "QRO": [
        "ibm_qrcs_engineering-dg@ibm.com",
        "fvargas@mx1.ibm.com",
        "saguilar@mx1.ibm.com",
        "garcizam@mx1.ibm.com",
        "agomsan@mx1.ibm.com"
    ],
    "TULT": [
        "almacen.tult@empresa.com",
        "lider.tult@empresa.com"
    ]
}

# =========================
# CARGA INVENTARIO
# =========================
def cargar_inventario_mysql(localidad_cod):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            marca,
            componente,
            descripcion,
            fru_ibm,
            su_po,
            oem_propio,
            cantidad,
            recibido,
            cantidad_actual,
            verificacion
        FROM kit_partes
        WHERE localidad = %s
        ORDER BY marca, componente
    """, (localidad_cod,))

    rows = cursor.fetchall()
    cursor.close()
    db.close()

    inventario = []

    for row in rows:
        inventario.append({
            "fila_excel": None,  # compatibilidad
            "Marca": row["marca"],
            "Componente": row["componente"],
            "Descripcion": row["descripcion"],
            "NumeroParte": row["fru_ibm"],
            "SUPO": row["su_po"],
            "OEM": row["oem_propio"],
            "CantidadOriginal": row["cantidad"] or 0,
            "FechaIngreso": row["recibido"],
            "CantidadActual": row["cantidad_actual"] or 0,
            "Verificado": row["verificacion"]
        })

    return inventario

# Alias de compatibilidad para módulos antiguos
cargar_inventario = cargar_inventario_mysql

def obtener_aviso_inventario_mysql(localidad_cod, dias_alerta=25):
    """
    Retorna None o un dict con aviso de inventariado mensual (MySQL)
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT MAX(created_at) AS fecha
        FROM kit_partes
        WHERE localidad = %s
          AND verificacion = 'CERRADO'
    """, (localidad_cod,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    fecha = row["fecha"] if row else None

    # ❌ Nunca se ha cerrado inventario
    if not fecha:
        return {
            "tipo": "danger",
            "mensaje": "⚠️ Este inventario aún no ha sido realizado."
        }

    if not isinstance(fecha, datetime):
        return {
            "tipo": "danger",
            "mensaje": "⚠️ Fecha de último inventario inválida."
        }

    dias = (datetime.now() - fecha).days

    if dias >= 30:
        return {
            "tipo": "danger",
            "mensaje": f"⚠️ Inventario vencido ({dias} días). Debe realizarse nuevamente."
        }

    if dias >= dias_alerta:
        return {
            "tipo": "warning",
            "mensaje": f"⏰ Inventario próximo a vencer ({dias} días)."
        }

    return {
        "tipo": "success",
        "mensaje": f"✔ Inventario vigente ({dias} días)."
    }

def generar_resumen_inventario_mysql(localidad_cod):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(verificacion = 'OK') AS ok,
            SUM(verificacion = 'DIF') AS dif
        FROM kit_partes
        WHERE localidad = %s
    """, (localidad_cod,))

    resumen = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "total": resumen["total"] or 0,
        "ok": resumen["ok"] or 0,
        "dif": resumen["dif"] or 0
    }

@kit_bp.route("/kit_partes", methods=["GET", "POST"])
def kit_partes():

    user_localidad = session.get("localidad") or ""
    user_role = session.get("rol") or ""

    inventario_localidad = request.form.get(
        "inventario_localidad",
        MAP_LOCALIDAD.get(user_localidad)
    )

    if inventario_localidad not in ("QRO", "TULT"):
        abort(400)

    localidad_usuario_cod = MAP_LOCALIDAD.get(user_localidad)

    # =========================
    # INVENTARIO MYSQL
    # =========================
    inventario = cargar_inventario_mysql(inventario_localidad)

    mensajes_stock_bajo = obtener_mensajes_stock_bajo(
        inventario_localidad,
    )

    inventario_cerrado = any(
        str(parte.get("Verificado")).upper() == "CERRADO"
        for parte in inventario
    )

    aviso_inventario = obtener_aviso_inventario_mysql(inventario_localidad)

    # =========================
    # 🔍 BUSCADOR MYSQL
    # =========================

    resultado_busqueda = None
    termino = request.args.get("buscar_parte")

    if termino:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT *
            FROM kit_partes
            WHERE fru_ibm LIKE %s
            AND localidad = %s
        """, (f"%{termino}%", inventario_localidad))
        filas = cursor.fetchall()
        cursor.close()
        conn.close()

        if filas:
            # Preparar resumen de búsqueda
            total = sum(p['cantidad'] or 0 for p in filas)
            disponibles = sum(p['cantidad_actual'] or 0 for p in filas)
            ok = sum(1 for p in filas if str(p.get('verificacion')).upper() == 'OK')
            dif = sum(1 for p in filas if str(p.get('verificacion')).upper() == 'DIF')

            resultado_busqueda = {
                "total": total,
                "disponibles": disponibles,
                "ok": ok,
                "dif": dif,
                "filas": filas
            }
        else:
            flash(f"❌ No se encontró ninguna parte con '{termino}' en {inventario_localidad}.", "warning")


    return render_template(
        "Kit_Partes.html",
        inventario_localidad=inventario_localidad,
        inventario=inventario,
        mensajes_stock_bajo=mensajes_stock_bajo,
        localidad_usuario_cod=localidad_usuario_cod,
        inventario_cerrado=inventario_cerrado,
        resultado_busqueda=resultado_busqueda,
        user_role=user_role,
        aviso_inventario=aviso_inventario
    )

#-------------------------------------
# ACTUALIZAR STOCK EN MYSQL (AJAX)
#-------------------------------------
@kit_bp.route("/actualizar_stock", methods=["POST"])
def actualizar_stock():

    user = session.get("user", {})
    rol = user.get("role") or session.get("rol")

    if rol not in ("ADMIN", "ENGINEER"):
        return jsonify({
            "status": "error",
            "mensaje": "No autorizado"
        })

    data = request.get_json()

    numero_parte = data.get("numero_parte")
    cantidad = int(data.get("cantidad", 0))
    accion = data.get("accion")  # "sumar" | "restar"

    if not numero_parte or cantidad <= 0 or accion not in ("sumar", "restar"):
        return jsonify({
            "status": "error",
            "mensaje": "Datos inválidos"
        })

    user_localidad = user.get("localidad") or session.get("localidad")
    localidad_cod = MAP_LOCALIDAD.get(user_localidad)

    if not localidad_cod:
        return jsonify({
            "status": "error",
            "mensaje": "Localidad inválida"
        })

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT cantidad, cantidad_actual
        FROM kit_partes
        WHERE fru_ibm = %s
          AND localidad = %s
    """, (numero_parte, localidad_cod))

    parte = cursor.fetchone()
    cursor.fetchall()

    if not parte:
        cursor.close()
        conn.close()
        return jsonify({
            "status": "error",
            "mensaje": "Parte no encontrada"
        })

    cantidad_original = parte["cantidad"] or 0
    cantidad_actual = parte["cantidad_actual"] or 0

    # ------------------
    # LÓGICA DE NEGOCIO
    # ------------------
    if accion == "sumar":
        nueva_cantidad = cantidad_actual + cantidad

        if nueva_cantidad > cantidad_original:
            cursor.close()
            conn.close()
            return jsonify({
                "status": "warning",
                "mensaje": "⚠️ No se puede exceder la cantidad original del kit"
            })

    else:  # restar
        if cantidad > cantidad_actual:
            cursor.close()
            conn.close()
            return jsonify({
                "status": "warning",
                "mensaje": "⚠️ No puedes retirar más de lo disponible"
            })

        nueva_cantidad = cantidad_actual - cantidad

    # ------------------
    # UPDATE
    # ------------------
    cursor.execute("""
        UPDATE kit_partes
        SET cantidad_actual = %s
        WHERE fru_ibm = %s
          AND localidad = %s
    """, (nueva_cantidad, numero_parte, localidad_cod))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "mensaje": "Stock actualizado correctamente",
        "nuevo_stock": nueva_cantidad
    })

#--------------------------------
#REGISTRAR NUEVA PARTE
#--------------------------------
@kit_bp.route("/registrar_parte_nueva", methods=["POST"])
def registrar_parte_nueva():

    from db import get_connection

    localidad_cod = request.form.get("inventario_localidad")
    if not localidad_cod:
        abort(400)

    # === Datos del formulario ===
    fru_ibm = request.form.get("NumeroParte")
    marca = request.form.get("Marca")
    componente = request.form.get("Componente")
    descripcion = request.form.get("Descripcion")
    su_po = request.form.get("SUPO")
    oem_propio = request.form.get("OEM")

    cantidad_original = int(request.form.get("CantidadOriginal", 0))
    cantidad_actual = int(request.form.get("CantidadActual", cantidad_original))
    recibido = request.form.get("FechaIngreso") or datetime.now().strftime("%Y-%m-%d")

    if not fru_ibm:
        flash("El número de parte (FRU) es obligatorio.", "danger")
        return redirect(url_for("kit_bp.kit_partes"))

    # === INSERT MySQL ===
    db = get_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO kit_partes (
                fru_ibm,
                marca,
                componente,
                descripcion,
                su_po,
                oem_propio,
                cantidad,
                recibido,
                cantidad_actual,
                verificacion,
                localidad
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            fru_ibm,
            marca,
            componente,
            descripcion,
            su_po,
            oem_propio,
            cantidad_original,
            recibido,
            cantidad_actual,
            None,
            localidad_cod
        ))

        db.commit()

        flash(
            f"Parte {fru_ibm} registrada correctamente en inventario {localidad_cod}.",
            "success"
        )

    except Exception as e:
        db.rollback()
        flash(f"Error al registrar la parte: {e}", "danger")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("kit_bp.kit_partes", inventario_localidad=localidad_cod))

#-------------------------------------
# ELIMINAR PARTE EN MYSQL (CORREGIDO)
#-------------------------------------
@kit_bp.route("/eliminar_parte", methods=["POST"])
def eliminar_parte():

    user = session.get("user")
    print("ROL EN SESIÓN:", session.get("role"))

    if not user or user.get("role") != "ADMIN":
        abort(403)

    numero_parte = request.form.get("fru_ibm")
    if not numero_parte:
        abort(400, "Número de parte inválido")

    # Localidad REAL del usuario
    user_localidad = user.get("localidad") or session.get("localidad")
    user_localidad_cod = MAP_LOCALIDAD.get(user_localidad)

    if not user_localidad_cod:
        abort(400, "Localidad inválida o no mapeada")

    # Seguridad dura: admin SOLO su localidad
    inventario_localidad = request.form.get("inventario_localidad") or user_localidad_cod
    if inventario_localidad != user_localidad_cod:
        abort(403)

    conn = get_connection()

    try:
        # Abrimos un cursor para SELECT
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id
            FROM kit_partes
            WHERE fru_ibm = %s
              AND localidad = %s
        """, (numero_parte, inventario_localidad))

        parte = cursor.fetchone()

        # 🔹 Consumir cualquier resultado pendiente
        cursor.fetchall()

        cursor.close()  # Cerramos cursor SELECT antes de DELETE

        if not parte:
            conn.close()
            abort(404, "Parte no encontrada")

        # Abrimos un NUEVO cursor para DELETE
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM kit_partes
            WHERE fru_ibm = %s
              AND localidad = %s
        """, (numero_parte, inventario_localidad))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Parte {numero_parte} eliminada correctamente.", "success")
        return redirect(url_for("kit_bp.kit_partes", inventario_localidad=inventario_localidad))

    except Exception as e:
        # Aseguramos cierre de conexión ante cualquier error
        conn.close()
        abort(500, f"Error interno: {e}")

#----------------------------------
# VERIFICAR INVENTARIO EN MYSQL
#----------------------------------
@kit_bp.route("/verificar_inventario", methods=["POST"])
def verificar_inventario():

    user = session.get("user", {})
    rol = user.get("role") or session.get("rol")

    if rol not in ("ADMIN", "ENGINEER"):
        abort(403)

    fru_ibm = request.form.get("fru_ibm")
    estado = request.form.get("estado")  # OK | DIF

    if not fru_ibm or estado not in ("OK", "DIF"):
        abort(400, "Datos inválidos")

    user_localidad = session.get("localidad")
    localidad_cod = MAP_LOCALIDAD.get(user_localidad)

    if not localidad_cod:
        abort(400, "Localidad inválida")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE kit_partes
        SET verificacion = %s
        WHERE fru_ibm = %s
          AND localidad = %s
    """, (estado, fru_ibm, localidad_cod))

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        abort(404, "Parte no encontrada")

    conn.commit()
    cursor.close()
    conn.close()

    flash(
        f"Inventario verificado para {fru_ibm}: {estado}",
        "success" if estado == "OK" else "warning"
    )

    return redirect(url_for("kit_bp.kit_partes"))

#-------------------------------------
# CERRAR INVENTARIO (MYSQL PURO)
#-------------------------------------
@kit_bp.route("/cerrar_inventario", methods=["POST"])
def cerrar_inventario():

    # =====================================================
    # 0️⃣ VALIDACIÓN DE USUARIO Y ROL
    # =====================================================
    user = session.get("user", {})
    if user.get("role") != "ADMIN":
        abort(403)

    # =====================================================
    # 1️⃣ LOCALIDAD (SEGURIDAD TOTAL)
    # =====================================================
    user_localidad_raw = session.get("localidad")
    user_localidad_cod = MAP_LOCALIDAD.get(user_localidad_raw)

    inventario_localidad_raw = (
        request.form.get("inventario_localidad") or user_localidad_raw
    )
    inventario_localidad_cod = MAP_LOCALIDAD.get(inventario_localidad_raw)

    if not user_localidad_cod or not inventario_localidad_cod:
        abort(400, "Localidad inválida")

    if inventario_localidad_cod != user_localidad_cod:
        abort(403)

    # =====================================================
    # 2️⃣ CONEXIÓN
    # =====================================================
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # =====================================================
    # 3️⃣ RESUMEN *ANTES* DE CERRAR (REEMPLAZO DE EXCEL)
    # =====================================================
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(verificacion = 'OK') AS ok,
            SUM(verificacion = 'DIF') AS dif
        FROM kit_partes
        WHERE localidad = %s
    """, (inventario_localidad_cod,))

    resumen = cursor.fetchone()

    total = resumen["total"] or 0
    ok = resumen["ok"] or 0
    dif = resumen["dif"] or 0

    # =====================================================
    # 4️⃣ REGISTRAR HISTÓRICO DE CIERRE
    # =====================================================
    cursor.execute("""
        INSERT INTO inventarios_cerrados
        (localidad, fecha_cierre, total, ok, dif, cerrado_por)
        VALUES (%s, NOW(), %s, %s, %s, %s)
    """, (
        inventario_localidad_cod,
        total,
        ok,
        dif,
        user.get("username") or user.get("email")
    ))

    # =====================================================
    # 5️⃣ MARCAR INVENTARIO COMO CERRADO
    # =====================================================
    cursor.execute("""
        UPDATE kit_partes
        SET verificacion = 'CERRADO'
        WHERE localidad = %s
    """, (inventario_localidad_cod,))

    conn.commit()
    cursor.close()
    conn.close()

    # =====================================================
    # 6️⃣ REPORTE / PDF / CORREO (MYSQL + REPORTLAB)
    # =====================================================

    from helpers.utils_correo import guardar_reporte_inventario_eml
    from datetime import datetime
    import os

    partes = obtener_partes_inventario(inventario_localidad_cod)
    resumen_calc = calcular_resumen_inventario(partes)

    ruta_pdf = generar_pdf_inventario(
        localidad=inventario_localidad_raw,
        partes=partes,
        resumen=resumen_calc
    )

    # Guardar referencia del último PDF en sesión
    session["ultimo_reporte_pdf"] = ruta_pdf

    # -----------------------------------------------------
    # Generar archivo .eml en lugar de abrir Outlook
    # -----------------------------------------------------

    # Nombre dinámico del archivo .eml
    nombre_eml = f"Inventario_{inventario_localidad_raw}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.eml"

    # Carpeta donde se guardará (asegúrate que exista o se cree)
    carpeta_reportes = "reportes_eml"
    os.makedirs(carpeta_reportes, exist_ok=True)

    ruta_eml = os.path.join(carpeta_reportes, nombre_eml)

    guardar_reporte_inventario_eml(
        ruta_pdf=ruta_pdf,
        localidad=inventario_localidad_raw,
        resumen=resumen_calc,
        ruta_salida=ruta_eml
    )

    # Opcional: guardar también en sesión si lo necesitas después
    session["ultimo_reporte_eml"] = ruta_eml


    # =====================================================
    # 7️⃣ MENSAJE FINAL
    # =====================================================
    flash(
        f"Inventario de {inventario_localidad_raw} cerrado correctamente | "
        f"Total: {total} | OK: {ok} | DIF: {dif}",
        "success"
    )

    return redirect(url_for("kit_bp.kit_partes"))

@kit_bp.route("/descargar_reporte_inventario")
def descargar_reporte_inventario():

    # =====================================================
    # VALIDACIÓN DE USUARIO
    # =====================================================
    user = session.get("user", {})
    if user.get("role") != "ADMIN":
        abort(403)

    # =====================================================
    # OBTENER RUTA DEL PDF
    # =====================================================
    ruta_pdf = session.get("ultimo_reporte_pdf")

    if not ruta_pdf or not os.path.exists(ruta_pdf):
        flash(
            "No hay un reporte de inventario disponible para descargar.",
            "warning"
        )
        return redirect(url_for("kit_bp.kit_partes"))

    # =====================================================
    # DESCARGA DEL ARCHIVO
    # =====================================================
    return send_file(
        ruta_pdf,
        as_attachment=True,
        download_name=os.path.basename(ruta_pdf)
    )

#-------------------------------------
# LIBERAR INVENTARIO (MYSQL)
#-------------------------------------
@kit_bp.route("/liberar_inventario", methods=["POST"])
def liberar_inventario():

    # =====================================================
    # 0️⃣ VALIDACIÓN DE USUARIO
    # =====================================================
    user = session.get("user", {})
    if user.get("role") != "ADMIN":
        abort(403)

    # =====================================================
    # 1️⃣ LOCALIDAD (SEGURIDAD)
    # =====================================================
    user_localidad_raw = session.get("localidad")
    user_localidad_cod = MAP_LOCALIDAD.get(user_localidad_raw)

    inventario_localidad_raw = (
        request.form.get("inventario_localidad") or user_localidad_raw
    )
    inventario_localidad_cod = MAP_LOCALIDAD.get(inventario_localidad_raw)

    if not user_localidad_cod or not inventario_localidad_cod:
        abort(400, "Localidad inválida")

    if inventario_localidad_cod != user_localidad_cod:
        abort(403)

    # =====================================================
    # 2️⃣ CONEXIÓN
    # =====================================================
    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # 3️⃣ LIBERAR INVENTARIO
    # =====================================================
    cursor.execute("""
        UPDATE kit_partes
        SET verificacion = 'PENDIENTE'
        WHERE localidad = %s
          AND verificacion = 'CERRADO'
    """, (inventario_localidad_cod,))

    filas_afectadas = cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    # =====================================================
    # 4️⃣ MENSAJE FINAL
    # =====================================================
    flash(
        f"Inventario de {inventario_localidad_raw} liberado correctamente "
        f"({filas_afectadas} partes reabiertas).",
        "success"
    )

    return redirect(url_for("kit_bp.kit_partes"))

#-----------------------------
#EDITAR PARTE
#----------------------------

@kit_bp.route("/editar_parte", methods=["GET", "POST"])
def editar_parte():

    if session.get("role") != "ADMIN":
        abort(403)

    fru = request.form.get("fru") or request.args.get("fru")
    localidad = request.values.get("localidad")
    print (session)
    print (localidad)
    if not fru or not localidad:
        abort(400)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM kit_partes
        WHERE fru_ibm = %s
        AND localidad = %s
    """, (fru, localidad))

    partes = cursor.fetchall()

    if not partes:
        abort(404)

    # Validar que NO haya DIF
    if any(p["cantidad_actual"] != p["cantidad"] for p in partes):
        flash("❌ No se puede editar una parte con diferencias de inventario.", "danger")
        return redirect(url_for("kit_bp.kit_partes"))

    if request.method == "POST":
        nueva_cantidad = request.form.get("cantidad")
        descripcion = request.form.get("descripcion")
        marca = request.form.get("marca")
        fru_nuevo = request.form.get("fru")

        cursor.execute("""
            UPDATE kit_partes
            SET
                fru_ibm = %s,
                descripcion = %s,
                marca = %s,
                cantidad = %s,
                cantidad_actual = %s
            WHERE fru_ibm = %s
            AND localidad = %s
        """, (
            fru_nuevo,
            descripcion,
            marca,
            nueva_cantidad,
            nueva_cantidad,
            fru,
            localidad
        ))

        conn.commit()
        flash("✅ Parte actualizada correctamente.", "success")

        cursor.close()
        conn.close()

        return redirect(url_for("kit_bp.kit_partes", buscar_parte=fru_nuevo))

    cursor.close()
    conn.close()

    return render_template(
        "Kit_Partes.html",
        resultado_busqueda=partes[0] if partes else None,
        fru=fru,
        localidad=localidad,
        inventario_localidad=localidad, # Para que coincida con tu input hidden
        current_role=session.get("role")
    )


