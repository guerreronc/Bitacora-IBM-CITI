import mysql.connector
from urllib.parse import urlparse
import os


def get_connection():
    try:
        database_url = os.environ.get("DATABASE_URL")

        url = urlparse(database_url)

        connection = mysql.connector.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path.lstrip("/")
        )

        print("CONEXION EXITOSA VIA URL")
        return connection

    except Exception as e:
        print("ERROR DE CONEXION:", e)
        return None
