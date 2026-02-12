from datetime import datetime, timedelta
from flask import request
from db import get_connection
from helpers.utils_inventario import obtener_mensajes_stock_bajo

MAP_LOCALIDAD = {
    "QUERETARO": "QRO",
    "QRO": "QRO",
    "TULTITLAN": "TULT",
    "TULT": "TULT"
}

def parsear_ventana(valor):
    if not valor:
        return None

    valor = valor.strip()

    # Si viene como rango "inicio - fin"
    if " - " in valor:
        valor = valor.split(" - ")[0].strip()

    valor = valor.replace("T", " ")

    # ISO / MySQL
    try:
        return datetime.fromisoformat(valor)
    except:
        pass

    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y"
    ]

    for f in formatos:
        try:
            return datetime.strptime(valor, f)
        except:
            continue

    return None

def obtener_alertas(usuario):
    alertas = []

    if not usuario:
        return alertas

    rol = usuario.get("role")
    if rol not in ("ADMIN", "ENGINEER"):
        return alertas

    localidad = usuario.get("localidad")
    if not localidad:
        return alertas

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            caso_ibm,
            status_principal,
            status,
            notas,
            ventana
        FROM casos
        WHERE status_principal = 'ABIERTO'
          AND localidad = %s
    """, (localidad,))

    casos = cursor.fetchall()

    ahora = datetime.now()
    limite = ahora + timedelta(minutes=180)

    for c in casos:

        # ============================
        # 1️⃣ CASO ABIERTO (INFORMATIVO)
        # ============================

        # Ventana (formato visual)
        ventana_txt = "Sin ventana"
        if c["ventana"]:
            try:
                dt = datetime.fromisoformat(c["ventana"])
                ventana_txt = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                ventana_txt = c["ventana"]

        # Notas legibles
        notas_txt = (c["notas"] or "Sin notas").replace("\n", "<br>")

        alertas.append({
            "tipo": "caso_abierto",
            "nivel": "info",
            "mensaje": (
                f"<strong>Caso:</strong> {c['caso_ibm']}<br>"
                f"<strong>Ventana:</strong> {ventana_txt}<br>"
                f"<strong>Status:</strong> {c['status'] or 'N/D'}<br>"
                f"<strong>Notas:</strong><br>"
                f"<div class='mt-1 text-muted' style='font-size:0.9em;'>"
                f"{notas_txt}</div>"
            )
        })

        # ============================
        # 2️⃣ SERVICIO PRÓXIMO / VENCIDO
        # ============================

        if not c["ventana"]:
            continue

        fecha_servicio = parsear_ventana(c["ventana"])
        if not fecha_servicio:
            continue

        if ahora <= fecha_servicio <= limite:
            minutos = int((fecha_servicio - ahora).total_seconds() / 60)
            alertas.append({
                "tipo": "servicio_proximo",
                "nivel": "warning",
                "mensaje": (
                    f"⏰ Servicio próximo — "
                    f"Caso <strong>{c['caso_ibm']}</strong> "
                    f"({minutos} min)"
                )
            })

        elif fecha_servicio < ahora:
            alertas.append({
                "tipo": "servicio_vencido",
                "nivel": "danger",
                "mensaje": (
                    f"❌ Servicio vencido — "
                    f"Caso <strong>{c['caso_ibm']}</strong>"
                )
            })

    # ============================
    # 📦 STOCK BAJO
    # ============================

    localidad_raw = usuario.get("localidad")
    inventario_localidad = MAP_LOCALIDAD.get(localidad_raw)

    if inventario_localidad:
        mensajes_stock = obtener_mensajes_stock_bajo(inventario_localidad)
        for msg in mensajes_stock:
            alertas.append({
                "tipo": "stock_bajo",
                "nivel": "danger",
                "mensaje": msg
            })


    cursor.close()
    conn.close()

    return alertas


