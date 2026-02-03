from flask import Blueprint, render_template, request, session
from datetime import timedelta
from db import get_connection
from helpers.utils_tiempos import seconds_to_dhm

historico_casos_bp = Blueprint("historico_casos", __name__)

def formatear_tiempo_mysql(seconds):
    return seconds_to_dhm(seconds)
# -------------------------------------------------------------------
# RUTA PRINCIPAL
# -------------------------------------------------------------------
@historico_casos_bp.route("/Historico_Casos", methods=["GET", "POST"])
def historico_casos():

    mensaje = None
    casos = []

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)


    # ---------------------------------------------------------------
    # LEER CASOS (BASE)
    # ---------------------------------------------------------------
    cursor.execute("""
        SELECT
            caso_ibm,
            caso_citi,
            ingeniero,
            serie,
            hostname,
            marca,
            modelo,
            severidad,
            status,
            localidad,
            notas,
            vobo_sitio,
            vobo_cliente,
            tiempo_apertura,
            tiempo_analisis,
            tiempo_atencion,
            tiempo_reporte
        FROM casos
        WHERE caso_ibm IS NOT NULL
          AND TRIM(caso_ibm) <> ''
    """)

    rows = cursor.fetchall()
    todos_los_casos = []

    for row in rows:
        todos_los_casos.append({

            # IDENTIFICADORES
            "CASO IBM": row["caso_ibm"],
            "CASO CITI": row.get("caso_citi", ""),

            # DATOS GENERALES
            "INGENIERO": row.get("ingeniero"),
            "SERIE EQUIPO": row.get("serie"),
            "HOST NAME": row.get("hostname"),
            "MARCA": row.get("marca"),
            "MODELO": row.get("modelo"),
            "SEVERIDAD": row.get("severidad"),
            "STATUS": row.get("status"),
            "LOCALIDAD": row.get("localidad"),
            "NOTAS": row.get("notas"),
            "VOBO_SITIO": row.get("vobo_sitio"),
            "VOBO_CLIENTE": row.get("vobo_cliente"),

            # TIEMPOS (YA CALCULADOS)
            "TIEMPO APERTURA": formatear_tiempo_mysql(row.get("tiempo_apertura")),
            "TIEMPO ANALISIS": formatear_tiempo_mysql(row.get("tiempo_analisis")),
            "TIEMPO ATENCION": formatear_tiempo_mysql(row.get("tiempo_atencion")),
            "TIEMPO REPORTE": formatear_tiempo_mysql(row.get("tiempo_reporte")),

            # PARTES (SE LLENA DESPUÉS)
            "PARTES": []
        })

    # ---------------------------------------------------------------
    # LISTA DE LOCALIDADES
    # ---------------------------------------------------------------
    localidades = sorted(
        set(c["LOCALIDAD"] for c in todos_los_casos if c.get("LOCALIDAD"))
    )

    # ---------------------------------------------------------------
    # FILTROS
    # ---------------------------------------------------------------
    valor = ""
    tipo = ""
    localidad_usuario = session.get("localidad")

    if request.method == "POST":
        tipo = request.form.get("tipo")
        valor = request.form.get("valor", "").strip()
        localidad_usuario = request.form.get("localidad") or localidad_usuario

    # FILTRO POR LOCALIDAD
    casos_filtrados = [
        c for c in todos_los_casos
        if not localidad_usuario or c.get("LOCALIDAD") == localidad_usuario
    ]

    # FILTRO POR CASO
    if valor:
        valor_norm = valor.lower()

        if tipo == "IBM":
            casos = [c for c in casos_filtrados if c["CASO IBM"].lower() == valor_norm]
        elif tipo == "CITI":
            casos = [c for c in casos_filtrados if c["CASO CITI"].lower() == valor_norm]

        if not casos:
            mensaje = f"No se encontró el caso '{valor}'."
    else:
        casos = casos_filtrados

    # ---------------------------------------------------------------
    # ASOCIAR PARTES USADAS
    # ---------------------------------------------------------------
    for caso in casos:

        cursor.execute("""
            SELECT
                fecha,
                parte,
                marca,
                modelo,
                numero_parte_proveedor,
                fru_ibm,
                descripcion,
                serie_retirada,
                serie_instalada,
                ingeniero,
                work_order,
                orden_ibm,
                notas,
                cantidad,
                localidad,
                se_entrega
            FROM registro_partes_usadas
            WHERE caso_ibm = %s
        """, (caso["CASO IBM"],))

        partes_rows = cursor.fetchall()
        partes_caso = []

        for p in partes_rows:
            partes_caso.append({
                "FECHA": p.get("fecha"),
                "PARTE": p.get("parte"),
                "MARCA": p.get("marca"),
                "MODELO": p.get("modelo"),
                "NUM PARTE": p.get("numero_parte_proveedor"),
                "FRU": p.get("fru_ibm"),
                "DESCRIPCION": p.get("descripcion"),
                "SERIE RETIRADA": p.get("serie_retirada"),
                "SERIE INSTALADA": p.get("serie_instalada"),
                "INGENIERO": p.get("ingeniero"),
                "WORK ORDER": p.get("work_order"),
                "ORDEN IBM": p.get("orden_ibm"),
                "NOTAS": p.get("notas"),
                "CANTIDAD": p.get("cantidad"),
                "LOCALIDAD": p.get("localidad"),
                "INGENIERO CITI": p.get("se_entrega")
            })

        caso["PARTES"] = partes_caso

    cursor.close()
    conn.close()

    # ---------------------------------------------------------------
    # RENDER FINAL
    # ---------------------------------------------------------------
    return render_template(
        "Historico_Casos.html",
        casos=casos,
        mensaje=mensaje,
        localidades=localidades,
        localidad_usuario=localidad_usuario
    )
