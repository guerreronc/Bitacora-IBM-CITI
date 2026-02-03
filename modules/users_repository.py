# modules/users_repository.py
from db import get_connection

def obtener_ingenieros(localidad):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT name
        FROM usuarios
        WHERE role IN ('ENGINEER', 'ADMIN')
          AND activo = 1
          AND localidad = %s
          AND name IS NOT NULL
          AND name <> ''
        ORDER BY name
    """, (localidad,))

    ingenieros = [row["name"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return ingenieros

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuarios WHERE username = %s",
        (username,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user


def update_user(username, data, password=None):
    conn = get_connection()
    cursor = conn.cursor()

    fields = ["name=%s", "email=%s", "localidad=%s", "role=%s"]
    values = [
        data["name"],
        data["email"],
        data["localidad"],
        data["role"]
    ]

    if password:
        fields.append("password=%s")
        values.append(password)

    values.append(username)

    sql = f"""
        UPDATE usuarios
        SET {", ".join(fields)}
        WHERE username = %s
    """

    cursor.execute(sql, tuple(values))
    conn.commit()

    cursor.close()
    conn.close()

def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM usuarios WHERE username = %s",
        (username,)
    )
    conn.commit()

    cursor.close()
    conn.close()
