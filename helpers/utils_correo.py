def enviar_reporte_inventario_pdf(ruta_pdf, localidad, resumen):
    import win32com.client
    import pythoncom
    import os
    from datetime import datetime

    ruta_pdf = os.path.abspath(ruta_pdf)

    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el PDF: {ruta_pdf}")

    pythoncom.CoInitialize()

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        mail.Subject = f"Inventario Kit de Partes - {localidad} - {fecha}"

        mail.HTMLBody = f"""
        <p>Buen día,</p>

        <p>Se adjunta el <strong>reporte de inventario del Kit de Partes</strong>
        correspondiente a la localidad <strong>{localidad}</strong>.</p>

        <ul>
            <li>Total de partes: <strong>{resumen['total']}</strong></li>
            <li>Verificadas OK: <strong>{resumen['ok']}</strong></li>
            <li>Con diferencias (DIF): <strong>{resumen['dif']}</strong></li>
        </ul>

        <p>Este inventario fue cerrado correctamente en sistema.</p>

        <p>Saludos,<br>
        Sistema de Bitácora</p>
        """

        mail.Attachments.Add(ruta_pdf)
        mail.Display()

    finally:
        pythoncom.CoUninitialize()