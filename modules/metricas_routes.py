from flask import Blueprint, render_template, jsonify, request
from db import get_connection
from helpers.utils_tiempos import seconds_to_dhm

metricas_bp = Blueprint("metricas", __name__)

def seconds_to_hours(sec):
    if sec is None:
        return 0
    return round(sec / 3600, 2)

def seconds_to_dhm(sec):
    if sec is None:
        return "0m"
    sec = int(sec)
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m or not parts: parts.append(f"{m}m")
    return " ".join(parts)
# ---------------------------------------------------------
# Vista principal
# ---------------------------------------------------------
@metricas_bp.route("/metricas")
def metricas():
    return render_template("Metricas.html")


# ---------------------------------------------------------
# Utilidades
# ---------------------------------------------------------
def _to_hours(value):
    """
    Convierte valores de MySQL a horas (float).
    Se asume que ya vienen en horas o en formato numérico.
    """
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except Exception:
        return None


def _promedio(lista):
    validos = [v for v in lista if v is not None]
    return round(sum(validos) / len(validos), 2) if validos else 0


# ---------------------------------------------------------
# API – Localidades disponibles
# ---------------------------------------------------------
@metricas_bp.route("/metricas/api/localidades")
def api_localidades():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT localidad
        FROM casos
        WHERE localidad IS NOT NULL
        ORDER BY localidad
    """
    cursor.execute(query)
    localidades = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify(localidades)


# ---------------------------------------------------------
# API – Métricas por Localidad
# ---------------------------------------------------------
@metricas_bp.route("/metricas/api/metricas_localidad")
def api_metricas_localidad():
    localidad = request.args.get("localidad")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            caso_ibm,
            tiempo_apertura,
            tiempo_analisis,
            tiempo_atencion,
            tiempo_reporte,
            tiempo_cliente
        FROM casos
        WHERE localidad = %s
          AND caso_ibm IS NOT NULL
    """
    cursor.execute(query, (localidad,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    tiempos = {
        "apertura": [],
        "analisis": [],
        "atencion": [],
        "reporte": [],
        "cliente": []
    }

    casos = []

    for row in rows:
        casos.append(row["caso_ibm"])

        tiempos["apertura"].append(_to_hours(row["tiempo_apertura"]))
        tiempos["analisis"].append(_to_hours(row["tiempo_analisis"]))
        tiempos["atencion"].append(_to_hours(row["tiempo_atencion"]))
        tiempos["reporte"].append(_to_hours(row["tiempo_reporte"]))
        tiempos["cliente"].append(_to_hours(row["tiempo_cliente"]))

    promedios = {
        "apertura": _promedio(tiempos["apertura"]),
        "analisis": _promedio(tiempos["analisis"]),
        "atencion": _promedio(tiempos["atencion"]),
        "reporte": _promedio(tiempos["reporte"]),
        "cliente": _promedio(tiempos["cliente"]),
    }

    return jsonify({
        "localidad": localidad,
        "promedios": promedios,
        "casos": casos
    })


# ---------------------------------------------------------
# API – Detalle por Caso
# ---------------------------------------------------------
@metricas_bp.route("/metricas/api/detalle_caso")
def api_detalle_caso():
    caso_id = request.args.get("caso")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            tiempo_apertura,
            tiempo_analisis,
            tiempo_atencion,
            tiempo_cliente,
            tiempo_reporte
        FROM casos
        WHERE caso_ibm = %s
        LIMIT 1
    """
    cursor.execute(query, (caso_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return jsonify({"error": "Caso no encontrado"}), 404

    return jsonify({
        "caso": caso_id,

        # 🔹 NUMÉRICO (para Chart.js)
        "apertura_h": seconds_to_hours(row["tiempo_apertura"]),
        "analisis_h": seconds_to_hours(row["tiempo_analisis"]),
        "atencion_h": seconds_to_hours(row["tiempo_atencion"]),
        "cliente_h": seconds_to_hours(row["tiempo_cliente"]),
        "reporte_h": seconds_to_hours(row["tiempo_reporte"]),

        # 🔹 TEXTO (para tarjetas)
        "apertura_txt": seconds_to_dhm(row["tiempo_apertura"]),
        "analisis_txt": seconds_to_dhm(row["tiempo_analisis"]),
        "atencion_txt": seconds_to_dhm(row["tiempo_atencion"]),
        "cliente_txt": seconds_to_dhm(row["tiempo_cliente"]),
        "reporte_txt": seconds_to_dhm(row["tiempo_reporte"]),
    })
