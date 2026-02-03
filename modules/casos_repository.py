from db import get_connection

def listar_casos(localidad=None, id_caso=None, filtro=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            caso_ibm,
            caso_citi,
            ingeniero,
            serie,
            status,
            falla,
            caso_proveedor,
            fecha_apertura,
            needpart AS necesita_parte,
            status_principal,
            vobo_sitio,
            vobo_cliente,
            localidad
        FROM casos
        WHERE caso_ibm IS NOT NULL
          AND caso_ibm <> ''
    """

    params = []

    if localidad:
        query += " AND UPPER(localidad) = %s"
        params.append(localidad.upper())

    if id_caso:
        query += " AND caso_ibm = %s"
        params.append(id_caso)

    if filtro == "abiertos":
        query += " AND UPPER(status_principal) <> 'CERRADO'"

    if filtro == "cerrados":
        query += " AND UPPER(status_principal) = 'CERRADO'"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def obtener_caso_por_ibm(caso_ibm):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM casos
        WHERE caso_ibm = %s
        LIMIT 1
    """

    cursor.execute(query, (caso_ibm,))
    caso = cursor.fetchone()

    cursor.close()
    conn.close()

    return caso
