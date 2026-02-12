import mysql.connector
from mysql.connector import Error
import os


def get_connection():
    try:
        host = os.environ.get("MYSQLHOST")
        port = os.environ.get("MYSQLPORT")
        user = os.environ.get("MYSQLUSER")
        password = os.environ.get("MYSQL_PASSWORD")
        database = os.environ.get("MYSQL_DATABASE")

        print("HOST:", host)
        print("PORT:", port)
        print("USER:", user)
        print("DATABASE:", database)

        connection = mysql.connector.connect(
            host=host,
            port=int(port) if port else 3306,
            user=user,
            password=password,
            database=database
        )

        print("Conexión exitosa")
        return connection

    except Exception as e:
        print("ERROR REAL DE CONEXION:", e)
        return None
