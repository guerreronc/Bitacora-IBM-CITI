from datetime import date, datetime

def evaluar_garantia(fecha_garantia):
    """
    fecha_garantia: date | datetime | None
    """

    if not fecha_garantia:
        return {
            "texto": "Garantía no registrada",
            "color": "#6c757d",
            "vigente": False
        }

    # Normalizar a date
    if isinstance(fecha_garantia, datetime):
        fecha_garantia = fecha_garantia.date()

    hoy = date.today()

    if fecha_garantia >= hoy:
        return {
            "texto": f"Equipo en garantía hasta {fecha_garantia:%d/%m/%Y}",
            "color": "#198754",
            "vigente": True
        }
    else:
        return {
            "texto": f"Garantía vencida el {fecha_garantia:%d/%m/%Y}",
            "color": "#dc3545",
            "vigente": False
        }
