# update_localidad.py
from db import get_connection

# Mapeo de localidades según tu indicación
localidades = {
    "ozamora": "TULTITLAN",
    "cnegrete": "QUERETARO",
    "aramirez": "QUERETARO",
    "dgarcia": "QUERETARO",
    "invitado": "QUERETARO",
    "Saguilar": "QUERETARO",
    "garcizam":"QUERETARO",
    "CitiGuest":"QUERETARO"
}

conn = get_connection()
cursor = conn.cursor()

for username, loc in localidades.items():
    cursor.execute("UPDATE usuarios SET localidad = %s WHERE username = %s", (loc, username))
    print(f"Usuario {username} actualizado con localidad {loc}.")

conn.commit()
cursor.close()
conn.close()
print("Actualización de localidades completada.")
