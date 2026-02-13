# utils_correo.py
import os
from email.message import EmailMessage
from datetime import datetime

# Configuración de destinatarios por localidad
DESTINATARIOS_POR_LOCALIDAD = {
    "QUERETARO": [
        "ibm_qrcs_engineering-dg@ibm.com",
        "fvargas@mx1.ibm.com",
        "saguilar@mx1.ibm.com",
        "garcizam@mx1.ibm.com",
        "agomsan@mx1.ibm.com",
    ],
    "TULTITLAN": [
        "soporte.tulti@empresa.com",
        "infraestructura.tulti@empresa.com",
    ]
}


def guardar_reporte_inventario_eml(
    ruta_pdf: str,
    localidad: str,
    resumen: dict,
    ruta_salida: str,
    usuario: dict
):
    """
    Genera un archivo .eml con el reporte de inventario del Kit de Partes.
    
    Parámetros:
    - ruta_pdf: ruta al PDF que se adjunta
    - localidad: nombre de la localidad
    - resumen: dict con keys 'total', 'ok', 'dif'
    - ruta_salida: ruta donde se guardará el archivo .eml
    - usuario: dict con datos del usuario logeado, mínimo 'email' y 'name' o 'username'
    """

    # Validar PDF
    ruta_pdf = os.path.abspath(ruta_pdf)
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el PDF: {ruta_pdf}")

    # -------------------------------
    # Configurar From (quien envía)
    # -------------------------------
    email_usuario = usuario.get("email") or "noreply@tudominio.com"
    nombre_usuario = usuario.get("name") or usuario.get("username") or "Sistema"
    from_header = f"{nombre_usuario} <{email_usuario}>"

    # -------------------------------
    # Configurar To (destinatarios según localidad)
    # -------------------------------
    lista_destinatarios = DESTINATARIOS_POR_LOCALIDAD.get(localidad.upper(), [])
    if not lista_destinatarios:
        raise ValueError(f"No hay destinatarios configurados para la localidad: {localidad}")
    to_header = ", ".join(lista_destinatarios)

    # -------------------------------
    # Construir mensaje
    # -------------------------------
    msg = EmailMessage()
    msg["From"] = from_header
    msg["To"] = to_header
    msg["Subject"] = f"Inventario Kit de Partes - {localidad} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    # Contenido HTML del correo
    html_content = f"""
    <p>Buen día,</p>
    <p>Se adjunta el reporte de inventario del Kit de Partes correspondiente a la localidad <strong>{localidad}</strong>.</p>
    <ul>
        <li>Total de partes: {resumen.get('total', 0)}</li>
        <li>Verificadas OK: {resumen.get('ok', 0)}</li>
        <li>Con diferencias (DIF): {resumen.get('dif', 0)}</li>
    </ul>
    <p>Saludos,<br>Sistema de Bitácora</p>
    """
    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(html_content, subtype="html")

    # -------------------------------
    # Adjuntar PDF
    # -------------------------------
    with open(ruta_pdf, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(ruta_pdf)
        )

    # -------------------------------
    # Crear carpeta de salida si no existe
    # -------------------------------
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    # -------------------------------
    # Guardar .eml en disco
    # -------------------------------
    with open(ruta_salida, "wb") as f:
        f.write(msg.as_bytes())

    print(f"[INFO] Correo guardado como .eml en {ruta_salida}")
