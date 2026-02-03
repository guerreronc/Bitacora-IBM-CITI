from db import get_connection

# =====================================================
# MENSAJES DE STOCK BAJO
# =====================================================
def obtener_mensajes_stock_bajo(localidad):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT fru_ibm, cantidad_actual, cantidad
        FROM kit_partes
        WHERE localidad = %s
    """, (localidad,))

    inventario = cursor.fetchall()
    cursor.close()
    db.close()

    mensajes = []

    for parte in inventario:
        actual = parte.get("cantidad_actual", 0) or 0
        original = parte.get("cantidad", 0) or 0

        if actual < original:
            faltante = original - actual
            mensajes.append(f"{parte['fru_ibm']} - Faltante: {faltante}")

    return mensajes

# =====================================================
# PARTES DEL INVENTARIO
# =====================================================
def obtener_partes_inventario(localidad_cod):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            marca,
            componente,
            descripcion,
            fru_ibm,
            cantidad AS cantidad_original,
            cantidad_actual,
            verificacion AS estado_inventario
        FROM kit_partes
        WHERE localidad = %s
        ORDER BY componente, descripcion
    """, (localidad_cod,))

    partes = cursor.fetchall()
    cursor.close()
    conn.close()

    return partes

# =====================================================
# RESUMEN DE INVENTARIO
# =====================================================
def calcular_resumen_inventario(partes):
    resumen = {
        "total": len(partes),
        "ok": 0,
        "dif": 0
    }

    for p in partes:
        if p.get("estado_inventario") == "OK":
            resumen["ok"] += 1
        elif p.get("estado_inventario") == "DIF":
            resumen["dif"] += 1

    return resumen
