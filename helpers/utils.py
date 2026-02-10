################################### UTILS.PY #######################################
# helpers/utils.py

import json
from datetime import datetime, timedelta

from config import USERS_FILE
from db import get_connection
# ============================================================================
# FECHAS / TIEMPOS
# ============================================================================

def to_dt(valor):
    """
    Convierte string ISO (YYYY-MM-DDTHH:MM) a datetime
    """
    try:
        return datetime.fromisoformat(valor) if valor else None
    except:
        return None


def _format_tdelta(delta):
    """
    Formatea un timedelta a 'Xd HH:MM'
    """
    if not delta or not isinstance(delta, timedelta):
        return "-"

    dias = delta.days
    horas, rem = divmod(delta.seconds, 3600)
    minutos = rem // 60

    if dias > 0:
        return f"{dias}d {horas:02d}:{minutos:02d}"
    return f"{horas:02d}:{minutos:02d}"


def calcular_tiempos(
    fecha_alerta,
    fecha_apertura,
    fecha_analisis,
    fecha_atencion,
    fecha_reporte
):
    """
    Calcula tiempos del caso y devuelve un dict listo para el HTML
    """
    tiempos = {
        "tiempo_apertura": "-",
        "tiempo_analisis": "-",
        "tiempo_atencion": "-",
        "tiempo_reporte": "-"
    }

    try:
        if fecha_alerta and fecha_apertura:
            tiempos["tiempo_apertura"] = _format_tdelta(fecha_apertura - fecha_alerta)

        if fecha_apertura and fecha_analisis:
            tiempos["tiempo_analisis"] = _format_tdelta(fecha_analisis - fecha_apertura)

        if fecha_analisis and fecha_atencion:
            tiempos["tiempo_atencion"] = _format_tdelta(fecha_atencion - fecha_analisis)

        if fecha_atencion and fecha_reporte:
            tiempos["tiempo_reporte"] = _format_tdelta(fecha_reporte - fecha_atencion)

    except Exception:
        pass

    return tiempos

# ============================================================================
# USUARIOS
# ============================================================================
def save_users(users):
    """Guarda lista de usuarios en MySQL"""
    conn = get_connection()
    cursor = conn.cursor()

    for u in users:
        username = u.get("username")
        password = u.get("password")
        role = u.get("role")
        activo = u.get("activo", True)
        localidad = u.get("localidad", "")
        temp_password = u.get("temp_password", True)
        name = u.get("name", "")
        email = u.get("email", "")

        cursor.execute("""
            INSERT INTO usuarios (username, password, role, activo, localidad, temp_password, name, email)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE password=%s, role=%s, activo=%s, localidad=%s, temp_password=%s, name=%s, email=%s
        """, (
            username, password, role, activo, localidad, temp_password, name, email,
            password, role, activo, localidad, temp_password, name, email
        ))

    conn.commit()
    cursor.close()
    conn.close()
# ============================================================================
# ICONOS DE ARCHIVOS
# ============================================================================

def icono_archivo(filename):
    ext = filename.split(".")[-1].lower()

    if ext in ["xls", "xlsx"]:
        return "📊"
    elif ext in ["rar", "zip"]:
        return "🗜️"
    elif ext in ["adu"]:
        return "💾"
    elif ext in ["txt", "log"]:
        return "📄"
    elif ext in ["pdf"]:
        return "📕"
    else:
        return "📁"
