import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Popocaca1203",
            database="bitacora_ibm_citi"
        )
        return connection
    except Error as e:
        print("Error al conectar a MySQL:", e)
        return None
