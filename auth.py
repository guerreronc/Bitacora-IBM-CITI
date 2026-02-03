# modules/auth.py
from db import get_connection

def load_users():
    """Carga todos los usuarios desde MySQL"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, password, role, activo, localidad, temp_password, name, email
        FROM usuarios
    """)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios

def authenticate(username, password):
    """Verifica usuario y contraseña contra MySQL"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, password, role, activo, localidad, temp_password, name, email
        FROM usuarios
        WHERE username = %s
    """, (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and user["password"] == password and user["activo"]:
        return user
    return None
