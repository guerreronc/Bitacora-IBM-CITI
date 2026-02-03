from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import os

def generar_pdf_inventario(localidad, partes, resumen):
    os.makedirs("exports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    ruta_pdf = f"exports/Inventario_Kit_{localidad}_{timestamp}.pdf"

    doc = SimpleDocTemplate(ruta_pdf, pagesize=LETTER)
    styles = getSampleStyleSheet()
    elementos = []

    # ----- TITULO -----
    elementos.append(Paragraph(
        f"<b>Inventario Kit de Partes – {localidad}</b>",
        styles["Title"]
    ))

    elementos.append(Paragraph(
        f"Fecha de cierre: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))

    # ----- RESUMEN -----
    elementos.append(Paragraph(
        f"Total: {resumen['total']} &nbsp;&nbsp;"
        f"OK: {resumen['ok']} &nbsp;&nbsp;"
        f"DIF: {resumen['dif']}",
        styles["Normal"]
    ))

    elementos.append(Paragraph("<br/>", styles["Normal"]))

    # ----- TABLA DE PARTES -----
    data = [[
        "Marca", "Componente", "Descripción",
        "Parte", "Orig", "Actual", "Estado"
    ]]

    for p in partes:
        data.append([
            p.get("marca", ""),
            p.get("componente", ""),
            p.get("descripcion", ""),
            p.get("fru_ibm", ""),
            p.get("cantidad", 0),
            p.get("cantidad_actual", 0),
            p.get("estado_inventario", "")
        ])

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (4,1), (-2,-1), "CENTER"),
    ]))

    # ----- COLOREAR ESTADO AUTOMÁTICO -----
    for i, p in enumerate(partes, start=1):
        estado = p.get("estado_inventario", "")
        if estado == "DIF":
            tabla.setStyle(TableStyle([
                ("TEXTCOLOR", (-1, i), (-1, i), colors.red)
            ]))
        elif estado == "OK":
            tabla.setStyle(TableStyle([
                ("TEXTCOLOR", (-1, i), (-1, i), colors.green)
            ]))

    elementos.append(tabla)
    doc.build(elementos)

    return ruta_pdf
