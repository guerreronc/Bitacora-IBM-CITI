import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Popocaca1203",
            database="bitacora_ibm_citi"
        )

    if conn.is_connected():
        print("✅ Conexión MySQL exitosa")

except Error as e:
    print("❌ Error de conexión:", e)

finally:
    if 'conn' in locals() and conn.is_connected():
        conn.close()
