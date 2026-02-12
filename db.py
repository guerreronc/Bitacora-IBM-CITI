import mysql.connector
from mysql.connector import Error
import os


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("MYSQLHOST"),
            port=int(os.environ.get("MYSQLPORT", 3306)),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE")
        )
        return connection
    except Error as e:
        print("Error al conectar a MySQL:", e)
        return None
