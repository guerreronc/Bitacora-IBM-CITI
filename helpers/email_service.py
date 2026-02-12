import os
import smtplib
from email.message import EmailMessage


def enviar_correo(to, cc, subject, html_body):
    msg = EmailMessage()
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = to
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = cc

    msg.set_content("Este correo requiere cliente compatible con HTML.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
        server.send_message(msg)
