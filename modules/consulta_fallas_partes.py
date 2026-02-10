from flask import Blueprint, render_template, request, session
from db import get_connection

consulta_fallas_partes_bp = Blueprint(
    "consulta_fallas_partes",
    __name__,
    url_prefix="/consulta-fallas-partes"
)

LOCALIDADES_VALIDAS = ["QUERETARO", "TULTITLAN"]


@consulta_fallas_partes_bp.route("/")
def resumen_fallas():
    localidad_filtro = request.args.get("localidad")
    localidad_sesion = session.get("localidad")
    localidad_activa = localidad_filtro or localidad_sesion

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    where_localidad = ""
    params = []

    if localidad_activa in LOCALIDADES_VALIDAS:
        where_localidad = "AND localidad = %s"
        params.append(localidad_activa)

    cursor.execute(f"""
        SELECT
            fru_ibm,
            descripcion,
            SUM(cantidad) AS total
        FROM registro_partes_usadas
        WHERE fru_ibm IS NOT NULL
          AND fru_ibm <> ''
          AND caso_ibm IS NOT NULL
          AND caso_ibm <> ''
          {where_localidad}
        GROUP BY fru_ibm, descripcion
        ORDER BY total DESC, MAX(fecha) DESC
        LIMIT 20
    """, params)

    rows = cursor.fetchall()

    top_partes = [(r["fru_ibm"], r["total"]) for r in rows]
    descripcion_por_fru = {
        r["fru_ibm"]: r["descripcion"] for r in rows
    }

    cursor.close()
    conn.close()

    return render_template(
    "consulta_fallas_partes.html",
    top_partes=top_partes,
    descripcion_por_fru=descripcion_por_fru,
    localidades=LOCALIDADES_VALIDAS,
    localidad_activa=localidad_activa,
    current_user=session.get("user", {}).get("name", "N/D"),
    current_role=session.get("user", {}).get("role", "N/D"),
    current_localidad=session.get("localidad", "N/D"),
)

@consulta_fallas_partes_bp.route("/<fru>")
def detalle_falla_parte(fru):
    localidad_filtro = request.args.get("localidad")
    localidad_sesion = session.get("localidad")
    localidad_activa = localidad_filtro or localidad_sesion

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Query con filtro opcional por localidad
    sql = """
        SELECT
            fecha,
            serie_equipo AS serie_servidor,
            host_name AS hostname,
            caso_ibm,
            caso_citi,
            ingeniero,
            se_entrega,
            work_order,
            orden_ibm,
            serie_instalada,
            serie_retirada,
            localidad,
            notas
        FROM registro_partes_usadas
        WHERE fru_ibm = %s
    """
    params = [fru]

    if localidad_activa in ["QUERETARO", "TULTITLAN"]:
        sql += " AND localidad = %s"
        params.append(localidad_activa)

    sql += " ORDER BY fecha DESC"

    cursor.execute(sql, params)
    detalle = cursor.fetchall()

    # Top partes (igual que antes)
    cursor.execute("""
        SELECT
            fru_ibm,
            descripcion,
            SUM(cantidad) AS total
        FROM registro_partes_usadas
        GROUP BY fru_ibm, descripcion
        ORDER BY total DESC, MAX(fecha) DESC
        LIMIT 20
    """)
    top = cursor.fetchall()
    top_partes = [(r["fru_ibm"], r["total"]) for r in top]
    descripcion_por_fru = {r["fru_ibm"]: r["descripcion"] for r in top}

    cursor.close()
    conn.close()

    return render_template(
        "consulta_fallas_partes.html",
        top_partes=top_partes,
        detalle_parte=detalle,
        parte_seleccionada=fru,
        descripcion_por_fru=descripcion_por_fru,
        current_user=session.get("usuario", "N/D"),
        current_role=session.get("rol", "N/D"),
        current_localidad=session.get("localidad", "N/D"),
        localidad_activa=localidad_activa  # para mantener la selección
    )

