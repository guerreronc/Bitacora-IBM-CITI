from datetime import datetime, timedelta
from helpers.utils import to_dt  # reutilizamos la misma función que ya tienes

def recalcular_tiempos_mysql(cursor, id_caso):
    """
    Reproduce la lógica de recalcular_tiempos_excel pero en MySQL.
    Lee los campos de fechas desde la tabla 'casos', calcula los tiempos
    (apertura, analisis, atencion, reporte, cliente) y hace un UPDATE.
    """
    # -------------------------
    # Leer los campos de fechas necesarios
    # -------------------------
    cursor.execute("""
        SELECT fecha, fecha_apertura, fecha_alerta,
               inicio_analisis, fin_analisis,
               inicio_atencion, fin_atencion,
               fecha_solucion
        FROM casos
        WHERE caso_ibm = %s
    """, (id_caso,))
    row = cursor.fetchone()
    if not row:
        return  # no existe el caso, salir

    def _safe_dt(v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return to_dt(v)
        return None

    f_alerta   = _safe_dt(row.get("fecha_alerta"))
    f_apertura = _safe_dt(row.get("fecha_apertura"))
    i_analisis = _safe_dt(row.get("inicio_analisis"))
    f_analisis = _safe_dt(row.get("fin_analisis"))
    i_atencion = _safe_dt(row.get("inicio_atencion"))
    f_atencion = _safe_dt(row.get("fin_atencion"))
    f_solucion = _safe_dt(row.get("fecha_solucion"))

    # -------------------------
    # Calcular los tiempos
    # -------------------------
    t_apertura = (f_apertura - f_alerta) if f_alerta and f_apertura else None
    t_analisis = (f_analisis - i_analisis) if i_analisis and f_analisis else None
    t_atencion = (f_atencion - i_atencion) if i_atencion and f_atencion else None
    t_reporte  = (f_solucion - f_alerta) if f_alerta and f_solucion else None

    # Tiempo cliente
    if all(isinstance(t, timedelta) for t in [t_apertura, t_analisis, t_atencion, t_reporte]):
        tiempo_cliente = t_reporte - (t_apertura + t_analisis + t_atencion)
        if tiempo_cliente.total_seconds() < 0:
            tiempo_cliente = None
    else:
        tiempo_cliente = None

    # -------------------------
    # Convertir timedelta a horas decimales o minutos según convención
    # (opcional, aquí dejamos en segundos para mantener exacto)
    # -------------------------
    def td_to_str(td):
        if td is None:
            return None
        # Guardamos como total segundos
        return td.total_seconds()

    # -------------------------
    # Actualizar la base MySQL
    # -------------------------
    cursor.execute("""
        UPDATE casos
        SET tiempo_apertura = %s,
            tiempo_analisis = %s,
            tiempo_atencion = %s,
            tiempo_reporte  = %s,
            tiempo_cliente  = %s
        WHERE caso_ibm = %s
    """, (
        td_to_str(t_apertura),
        td_to_str(t_analisis),
        td_to_str(t_atencion),
        td_to_str(t_reporte),
        td_to_str(tiempo_cliente),
        id_caso
    ))

def to_dt_mysql(v):
    """
    Convierte valor de formulario o string a datetime para MySQL.
    NO calcula tiempos.
    """
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(v).date()
    except Exception:
        return None

def seconds_to_dhm(seconds):
    """
    Convierte segundos a string 'Xd Yh Zm'
    """
    if seconds is None:
        return "0m"

    try:
        seconds = int(seconds)
    except Exception:
        return "0m"

    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    hours = hours % 24
    minutes = minutes % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}m")

    return " ".join(parts)

