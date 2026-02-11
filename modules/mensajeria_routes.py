from datetime import datetime
import os
from flask import Blueprint, request, jsonify
from email.message import EmailMessage
from flask import send_file
import io
from helpers.utils_servidores_service import evaluar_garantia
from modules.base_servidores import obtener_servidor_por_serie

mensajeria_bp = Blueprint(
    "mensajeria_bp",
    __name__,
    url_prefix="/mensajeria"   # opcional pero recomendado
)

@mensajeria_bp.route("/correo_hdd_cliente", methods=["POST"])
def correo_hdd_cliente():
    datos = request.form
    localidad = datos.get("localidad", "").upper()
    #email = user.get("email")
    if localidad in ("QUERETARO", "QRO"):
        to = datos.get("gt.la.qrcs.ops@citi.com","")
        cc = "ibm_qrcs_engineering-dg@ibm.com;fvargas@mx1.ibm.com;saguilar@mx1.ibm.com;garcizam@mx1.ibm.com;agomsan@mx1.ibm.com"

    else:
        to = datos.get("correo_cliente", "")
        cc = "fvargas@mx1.ibm.com;agomsan@mx1.ibm.com"

    cuerpo = f"""
    
    <table width="100%" bgcolor="#f2f4f7" cellpadding="0" cellspacing="0">
    <tr>
    <td align="center" style="padding:20px 0;">

    <table width="600" cellpadding="0" cellspacing="0">
    <tr>

    <!-- TARJETA DISCO RETIRADO -->
    <td width="300" valign="top" style="padding-right:8px;">
    <table width="100%" cellpadding="0" cellspacing="0"
    style="background:#ffffff;border:1px solid #d0d7de;">
    <tr>
    <td style="
    background:#f59e0b;
    color:#ffffff;
    padding:14px;
    font-size:15px;
    font-weight:bold;
    font-family:Arial, Helvetica, sans-serif;">
    DISCO RETIRADO
    </td>
    </tr>
    <tr>
    <td style="padding:14px;font-family:Arial, Helvetica, sans-serif;font-size:13px;">
    <table width="100%" cellpadding="4">
    <tr><td><strong>Marca:</strong></td><td>{datos.get('marca','')}</td></tr>
    <tr><td><strong>Modelo:</strong></td><td>{datos.get('modelo','')}</td></tr>
    <tr><td><strong>No. Parte:</strong></td><td>{datos.get('num_proveedor','')}</td></tr>
    <tr><td><strong>Serie:</strong></td><td>{datos.get('serie_retirada','')}</td></tr>
    <tr><td><strong>Caso IBM:</strong></td><td>{datos.get('caso_ibm','')}</td></tr>
    <tr><td><strong>Host:</strong></td><td>{datos.get('host_name','')}</td></tr>
    <tr><td><strong>SLOT:</strong></td><td>{datos.get('ubicacion','')}</td></tr>
    </table>
    </td>
    </tr>
    </table>
    </td>

    <!-- TARJETA DISCO INSTALADO -->
    <td width="300" valign="top" style="padding-left:8px;">
    <table width="100%" cellpadding="0" cellspacing="0"
    style="background:#ffffff;border:1px solid #d0d7de;">
    <tr>
    <td style="
    background:#16a34a;
    color:#ffffff;
    padding:14px;
    font-size:15px;
    font-weight:bold;
    font-family:Arial, Helvetica, sans-serif;">
    DISCO INSTALADO
    </td>
    </tr>
    <tr>
    <td style="padding:14px;font-family:Arial, Helvetica, sans-serif;font-size:13px;">
    <table width="100%" cellpadding="4">
    <tr><td><strong>Marca:</strong></td><td>{datos.get('marca','')}</td></tr>
    <tr><td><strong>Modelo:</strong></td><td>{datos.get('modelo','')}</td></tr>
    <tr><td><strong>No. Parte:</strong></td><td>{datos.get('num_proveedor','')}</td></tr>
    <tr><td><strong>Serie:</strong></td><td>{datos.get('serie_instalada','')}</td></tr>
    <tr><td><strong>Caso IBM:</strong></td><td>{datos.get('caso_ibm','')}</td></tr>
    <tr><td><strong>Host:</strong></td><td>{datos.get('host_name','')}</td></tr>
    <tr><td><strong>SLOT:</strong></td><td>{datos.get('ubicacion','')}</td></tr>
    </table>
    </td>
    </tr>
    </table>
    </td>

    </tr>
    </table>

    <!-- FOOTER -->
    <table width="600" cellpadding="0" cellspacing="0">
    <tr>
    <td style="
    padding:12px;
    font-size:12px;
    color:#555;
    font-family:Arial, Helvetica, sans-serif;">
    Se entrega la parte retirada al ingeniero en turno de Citi:<br>
    <strong>{datos.get('personal_citi','')}</strong>
    </td>
    </tr>
    </table>

    </td>
    </tr>
    </table>
    """
        # 🔹 AQUÍ ES LO QUE TE FALTABA
    msg = EmailMessage()
    msg["Subject"] = "ENTREGA DE DISCO"
    msg["From"] = "email"
    msg["To"] = to
    msg["Cc"] = cc

    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(cuerpo, subtype="html")
    eml_buffer = io.BytesIO()
    eml_buffer.write(msg.as_bytes())
    eml_buffer.seek(0)

    filename = f"Correo_HDD_Caso_{datos.get('caso_ibm')}.eml"

    return send_file(
        eml_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="message/rfc822"
    )


@mensajeria_bp.route("/correo_writeoff", methods=["POST"])
def correo_writeoff():
    datos = request.form
    #email = user.get("email")
    # -----------------------------
    # DESTINATARIOS
    # -----------------------------
    localidad = datos.get("localidad", "").upper()

    if localidad in ("QUERETARO", "QRO"):
        to = "agomsan@mx1.ibm.com"
        cc = "IBM_QRCS_engineering-dg@ibm.com;saguilar@mx1.ibm.com;garcizam@mx1.ibm.com"
    else:
        to = ""
        cc = ""

    # -----------------------------
    # DATOS DEL SERVIDOR (YA RESUELTOS)
    # -----------------------------
    serie = datos.get("serie_equipo", "")
    hostname = datos.get("hostname", "")
    marca = datos.get("marca", "")
    modelo = datos.get("modelo", "")
    garantia_texto = datos.get("garantia_texto", "Garantía no registrada")
    garantia_color = datos.get("garantia_color", "#6c757d")
    
    fuera_garantia = False
    
    print("SERIE RECIBIDA:", serie)


    if serie:
        servidor = obtener_servidor_por_serie(serie)
        print(
            "Fecha garantía BD:",
            servidor.get("fecha_garantia"),
            type(servidor.get("fecha_garantia"))
        )


        if servidor and servidor.get("fecha_garantia"):
            resultado_garantia = evaluar_garantia(servidor["fecha_garantia"])
            garantia_texto = resultado_garantia["texto"]
            garantia_color = resultado_garantia["color"]

            # 👇 ESTA ES LA CLAVE
            if not resultado_garantia["vigente"]:
                fuera_garantia = True

    # -----------------------------
    # CARD SERVIDOR (OPCIONAL)
    # -----------------------------
    card_servidor = ""

    if serie:
        card_servidor = f"""
        <br>
        <table width="600" cellpadding="0" cellspacing="0"
          style="background:#ffffff;border:1px solid #2563eb;">
          <tr>
            <td style="background:#2563eb;color:#ffffff;
                       padding:14px;font-size:16px;
                       font-weight:bold;font-family:Arial;">
              Información del Servidor
            </td>
          </tr>
          <tr>
            <td style="padding:14px;font-family:Arial;">
              <table width="100%" cellpadding="6">
                <tr><td width="40%"><strong>Serie:</strong></td><td>{serie}</td></tr>
                <tr><td><strong>Hostname:</strong></td><td>{hostname}</td></tr>
                <tr><td><strong>Marca:</strong></td><td>{marca}</td></tr>
                <tr><td><strong>Modelo:</strong></td><td>{modelo}</td></tr>
                <tr>
                  <td><strong>Garantía:</strong></td>
                  <td style="color:{garantia_color};font-weight:bold;">
                    {garantia_texto}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        """
    card_fuera_garantia = ""

    if fuera_garantia:
        card_fuera_garantia = f"""
        <br>
        <table width="600" cellpadding="0" cellspacing="0"
          style="background:#fff1f2;border:1px solid #dc3545;">
          <tr>
            <td style="background:#dc3545;color:#ffffff;
                      padding:14px;font-size:16px;
                      font-weight:bold;font-family:Arial;">
              ⚠ SERVIDOR FUERA DE GARANTÍA
            </td>
          </tr>
          <tr>
            <td style="padding:14px;font-family:Arial;color:#7f1d1d;">
              El servidor con número de serie <strong>{serie}</strong>
              tiene la garantía <strong>VENCIDA</strong>.
              <br><br>
              El Write-Off solicitado corresponde a una parte
              fuera de cobertura de contrato.
            </td>
          </tr>
        </table>
        """
    # -----------------------------
    # CUERPO DEL CORREO
    # -----------------------------
    cuerpo = f"""
    <table width="100%" bgcolor="#f2f4f7" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding:20px 0;">

          <table width="600" cellpadding="0" cellspacing="0"
            style="background:#ffffff;border:1px solid #d0d7de;">

            <tr>
              <td style="background:#ef4444;color:#ffffff;
                         padding:16px;font-size:18px;
                         font-weight:bold;font-family:Arial;">
                WRITE OFF – SOLICITUD
              </td>
            </tr>

            <tr>
              <td style="padding:16px;font-family:Arial;">
                <table width="100%" cellpadding="6">
                  <tr><td width="40%"><strong>Ingeniero:</strong></td><td>{datos.get('ingeniero','')}</td></tr>
                  <tr><td><strong>Orden IBM:</strong></td><td>{datos.get('orden_ibm','')}</td></tr>
                  <tr><td><strong>Número de Parte (FRU):</strong></td><td>{datos.get('fru','')}</td></tr>
                  <tr><td><strong>Cantidad:</strong></td><td>{datos.get('cantidad','')}</td></tr>
                  <tr><td><strong>Caso IBM:</strong></td><td>{datos.get('caso_ibm','')}</td></tr>
                  <tr><td><strong>Work Order:</strong></td><td>{datos.get('work_order','')}</td></tr>
                </table>
              </td>
            </tr>

            <tr>
              <td style="background:#f8fafc;padding:12px;
                         font-size:12px;color:#555;
                         font-family:Arial;">
                Favor de revisar y autorizar el WriteOff de la siguiente parte.
              </td>
            </tr>

          </table>

          {card_servidor}
          {card_fuera_garantia}
        </td>
      </tr>
    </table>
    """
    # -----------------------------
    # GENERAR .EML EN MEMORIA
    # -----------------------------
    msg = EmailMessage()
    msg["From"] = "empresa@test"
    msg["To"] = to

    if cc:
        msg["Cc"] = cc

    msg["Subject"] = f"WRITE OFF - {datos.get('fru')} / {datos.get('orden_ibm')}"
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(cuerpo, subtype="html")

    # Crear archivo en memoria
    eml_bytes = io.BytesIO()
    eml_bytes.write(bytes(msg))
    eml_bytes.seek(0)

    nombre_archivo = f"WRITE_OFF_{datos.get('fru')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.eml"

    return send_file(
        eml_bytes,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="message/rfc822"
    ), jsonify({"mensaje": "Solicitud de WRITE-OFF generada correctamente"})


