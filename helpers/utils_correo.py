# utils_correo.py
import os
from email.message import EmailMessage
from datetime import datetime

def guardar_reporte_inventario_eml(ruta_pdf, localidad, resumen, ruta_salida):
    """
    Genera un archivo .eml con el reporte de inventario del Kit de Partes
    en vez de abrir Outlook (multiplataforma).

    ruta_pdf: ruta al PDF que se adjunta
    localidad: nombre de la localidad
    resumen: dict con keys 'total', 'ok', 'dif'
    ruta_salida: ruta donde se guardará el archivo .eml
    """

    ruta_pdf = os.path.abspath(ruta_pdf)

    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el PDF: {ruta_pdf}")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    msg = EmailMessage()
    msg['Subject'] = f"Inventario Kit de Partes - {localidad} - {fecha}"
    msg['From'] = 'sistema@example.com'  # cambiar según tu necesidad
    msg['To'] = 'destinatario@example.com'  # cambiar o parametrizar si quieres

    # Contenido HTML
    msg.set_content(f"""
Buen día,

Se adjunta el reporte de inventario del Kit de Partes
correspondiente a la localidad {localidad}.

Total de partes: {resumen['total']}
Verificadas OK: {resumen['ok']}
Con diferencias (DIF): {resumen['dif']}

Saludos,
Sistema de Bitácora
""")

    # Adjuntar PDF
    with open(ruta_pdf, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype='application',
            subtype='pdf',
            filename=os.path.basename(ruta_pdf)
        )

    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    # Guardar el .eml
    with open(ruta_salida, 'wb') as f:
        f.write(msg.as_bytes())

    print(f"Correo guardado como .eml en {ruta_salida}")
