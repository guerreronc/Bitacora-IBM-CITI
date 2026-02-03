from flask import Blueprint, render_template, request, jsonify
from db import get_connection

buscar_parte_bp = Blueprint(
    "buscar_parte",
    __name__,
    template_folder="templates"
)

# ================================
# FUNCIONES DE CONSULTA MYSQL
# ================================

def obtener_marcas():
    """Devuelve la lista de marcas únicas desde MySQL"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT marca
        FROM partes_fru
        WHERE marca IS NOT NULL
          AND TRIM(marca) <> ''
        ORDER BY marca
    """)

    marcas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return marcas


def obtener_componentes_por_marca(marca):
    """Devuelve la lista de COMPONENTES únicos para la marca seleccionada"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT componente
        FROM partes_fru
        WHERE marca = %s
          AND componente IS NOT NULL
          AND TRIM(componente) <> ''
        ORDER BY componente
    """, (marca,))

    componentes = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return componentes


def obtener_detalles_por_marca_componente(marca, componente):
    """Devuelve lista de diccionarios con los detalles de la parte"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT marca, componente, detalle, fru_ibm, spare_part, numero_parte
        FROM partes_fru
        WHERE marca = %s AND componente = %s
        ORDER BY fru_ibm
    """, (marca, componente))

    resultados = []
    for row in cursor.fetchall():
        resultados.append({
            "MARCA": row["marca"] or "",
            "COMPONENTE": row["componente"] or "",
            "DETALLE": row["detalle"] or "",
            "PN_IBM": row["fru_ibm"] or "",
            "SPARE_PART": row["spare_part"] or "",
            "PARTE": row["numero_parte"] or "N/A"
        })

    cursor.close()
    conn.close()
    return resultados


def buscar_por_fru(fru, parcial=True):
    """
    Busca registros por PN IBM (FRU) de manera flexible en MySQL.
    """
    fru = fru.strip().upper()
    if not fru:
        return []

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if parcial:
        like_pattern = f"%{fru}%"
        cursor.execute("""
            SELECT fru_ibm, numero_parte, spare_part, marca, componente, detalle
            FROM partes_fru
            WHERE UPPER(fru_ibm) LIKE %s
            ORDER BY fru_ibm
            LIMIT 50
        """, (like_pattern,))
    else:
        cursor.execute("""
            SELECT fru_ibm, numero_parte, spare_part, marca, componente, detalle
            FROM partes_fru
            WHERE UPPER(fru_ibm) = %s
            LIMIT 1
        """, (fru,))

    resultados = []
    for row in cursor.fetchall():
        resultados.append({
            "MARCA": row["marca"] or "",
            "COMPONENTE": row["componente"] or "",
            "DETALLE": row["detalle"] or "",
            "PN_IBM": row["fru_ibm"] or "",
            "SPARE_PART": row["spare_part"] or "",
            "PARTE": row["numero_parte"] or "N/A"
        })

    cursor.close()
    conn.close()
    return resultados


def registrar_parte(nueva_parte):
    """
    Registra una nueva parte en la tabla partes_fru.
    nueva_parte = {
        "MARCA": str,
        "COMPONENTE": str,
        "DETALLE": str,
        "PN_IBM": str,
        "SPARE_PART": str,
        "PARTE": str
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 🔴 VALIDAR DUPLICADO POR FRU (exacto)
    fru = nueva_parte.get("PN_IBM", "").strip()
    cursor.execute("""
        SELECT 1 FROM partes_fru WHERE fru_ibm = %s LIMIT 1
    """, (fru,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return {"status": "error", "msg": "Este PN IBM (FRU) ya existe en la base de datos."}

    # Insertar nueva parte
    cursor.execute("""
        INSERT INTO partes_fru (marca, componente, detalle, fru_ibm, spare_part, numero_parte)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        safe_str(nueva_parte.get("MARCA")),
        safe_str(nueva_parte.get("COMPONENTE")),
        safe_str(nueva_parte.get("DETALLE")),
        safe_str(nueva_parte.get("PN_IBM")),
        safe_str(nueva_parte.get("SPARE_PART")),
        safe_str(nueva_parte.get("PARTE"))
    ))

    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "ok", "msg": "Parte registrada correctamente."}

def safe_str(val):
    return str(val) if val is not None else ""

# ================================
# RUTAS
# ================================

@buscar_parte_bp.route("/buscar-parte")
def buscar_parte():
    marcas = obtener_marcas()
    return render_template(
        "buscar_partes.html",
        marcas=marcas
    )


@buscar_parte_bp.route("/buscar-parte/componentes", methods=["POST"])
def api_componentes_por_marca():
    data = request.json
    marca = data.get("marca", "").strip()
    if not marca:
        return jsonify([])
    componentes = obtener_componentes_por_marca(marca)
    return jsonify(componentes)


@buscar_parte_bp.route("/buscar-parte/detalles", methods=["POST"])
def api_detalles_por_marca_componente():
    data = request.json
    marca = data.get("marca", "").strip()
    componente = data.get("componente", "").strip()
    if not marca or not componente:
        return jsonify([])
    detalles = obtener_detalles_por_marca_componente(marca, componente)
    return jsonify(detalles)


@buscar_parte_bp.route("/buscar-parte/fru", methods=["POST"])
def api_buscar_fru():
    data = request.json
    fru = data.get("fru", "").strip()
    parcial = data.get("parcial", True)
    if not fru:
        return jsonify([])
    resultados = buscar_por_fru(fru, parcial=parcial)
    return jsonify(resultados)


@buscar_parte_bp.route("/buscar-parte/registrar", methods=["POST"])
def api_registrar_parte():
    data = request.json
    required_fields = ["MARCA", "COMPONENTE", "DETALLE", "PN_IBM"]

    for f in required_fields:
        if not data.get(f, "").strip():
            return jsonify({"status": "error", "msg": f"El campo {f} es obligatorio."})

    try:
        response = registrar_parte(data)
        return jsonify(response)
    except Exception as e:
        import traceback
        print("ERROR REGISTRAR PARTE:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "msg": str(e)})


@buscar_parte_bp.route("/buscar-parte/registrar", methods=["GET"])
def vista_registrar_parte():
    marcas = obtener_marcas()
    return render_template(
        "registrar_parte.html",
        marcas=marcas
    )

from flask import jsonify, session
from db import get_connection

@buscar_parte_bp.route("/buscar-parte/eliminar", methods=["POST"])
def eliminar_parte():
    user = session.get("user", {})
    if user.get("role") != "ADMIN":
        return jsonify({"success": False, "message": "No autorizado"}), 403

    data = request.json
    fru = data.get("fru_ibm", "").strip()

    if not fru:
        return jsonify({"success": False, "message": "FRU inválido"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM partes_fru WHERE fru_ibm = %s",
        (fru,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Parte eliminada correctamente"})

