import mysql.connector
from urllib.parse import urlparse
import os

print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL no está definida")

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

