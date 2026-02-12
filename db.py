def get_connection():
    try:
        connection = mysql.connector.connect(
            host="mysql.railway.internal",
            port=3306,
            user="root",
            password="hOxkDZyqVRVyhtorxAaWvhgFSKTerJuw",
            database="railway"
        )
        print("CONEXION HARDCODE EXITOSA")
        return connection
    except Exception as e:
        print("ERROR HARDCODE:", e)
        return None
