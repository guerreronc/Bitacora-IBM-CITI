from flask import Blueprint, render_template, request
from collections import defaultdict
from db import get_connection  # ajusta el import si tu ruta difiere

historico_fallas_bp = Blueprint(
    "historico_fallas",
    __name__,
    url_prefix="/historico"
)

# ---------------------------
# LECTURA DE CASOS (MYSQL)
# ---------------------------
def leer_casos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            seguimiento,
            caso_ibm,
            caso_citi,
            fecha_apertura,
            severidad,
            ingeniero,
            serie,
            hostname,
            ubicacion,
            marca,
            modelo,
            falla,
            notas,
            localidad
        FROM casos
        WHERE serie IS NOT NULL
          AND TRIM(serie) <> ''
    """
    cursor.execute(query)
    casos = cursor.fetchall()

    cursor.close()
    conn.close()
    return casos


# ---------------------------
# LECTURA DE PARTES (MYSQL)
# ---------------------------
def leer_partes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            caso_ibm,
            caso_citi,
            parte,
            marca,
            modelo,
            numero_parte_proveedor,
            fru_ibm,
            descripcion,
            serie_retirada,
            serie_instalada,
            work_order,
            ingeniero,
            se_entrega,
            fecha_entrega,
            notas,
            cantidad,
            localidad
        FROM registro_partes_usadas
    """
    cursor.execute(query)
    partes = cursor.fetchall()

    cursor.close()
    conn.close()
    return partes


# ---------------------------
# HISTÓRICO GENERAL
# ---------------------------
@historico_fallas_bp.route("/")
def historico():
    localidad = request.args.get("localidad")

    casos = leer_casos()
    localidades = sorted(
        set(c["localidad"] for c in casos if c.get("localidad"))
    )

    equipos = []

    if localidad:
        filtrados = [c for c in casos if c["localidad"] == localidad]
        agrupados = defaultdict(list)

        for c in filtrados:
            agrupados[c["serie"]].append(c)

        for serie, registros in agrupados.items():
            equipos.append({
                "serie": serie,
                "marca": registros[0]["marca"],
                "modelo": registros[0]["modelo"],
                "total_fallas": len(registros),
                "casos": registros
            })

        equipos.sort(key=lambda x: x["total_fallas"], reverse=True)

    top_equipos = equipos[:5]

    return render_template(
        "Historico_Fallas.html",
        localidades=localidades,
        localidad_sel=localidad,
        equipos=equipos,
        top_equipos=top_equipos
    )


# ---------------------------
# DETALLE DE CASO
# ---------------------------
@historico_fallas_bp.route("/caso/<caso_ibm>")
def detalle_caso(caso_ibm):
    casos = leer_casos()
    partes = leer_partes()

    caso = next(
        (c for c in casos if str(c["caso_ibm"]).strip() == str(caso_ibm).strip()),
        None
    )

    if not caso:
        return "Caso no encontrado", 404

    caso_ibm_limpio = str(caso["caso_ibm"]).strip()

    partes_caso = [
        p for p in partes
        if str(p.get("caso_ibm", "")).strip() == caso_ibm_limpio
    ]

    return render_template(
        "Historico_Fallas.html",
        detalle_caso=caso,
        partes=partes_caso
    )
