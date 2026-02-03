import csv
from db import get_connection
from datetime import datetime


ruta_csv = r"C:\Users\001256781\Desktop\CASOS.csv"

conn = get_connection()
cursor = conn.cursor()

def parse_datetime(valor):
    if not valor or str(valor).strip() == "":
        return None
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        return None
    
def parse_int(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == "":
        return None
    try:
        return int(float(valor))
    except ValueError:
        return None

with open(ruta_csv, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        sql = """ 
        INSERT INTO casos (
            fecha,alciti,seguimiento,caso_ibm,caso_citi,fecha_apertura,
            severidad,ingeniero,serie,hostname,ubicacion,marca,modelo,
            fecha_garantia,caso_proveedor,falla,ventana,status,tipo_servicio,
            needpart,ubicacion_parte,notas,status_principal,marca_csp,modelo_csp,fecha_alerta,
            fecha_solucion,inicio_analisis,fin_analisis,inicio_atencion,fin_atencion,tiempo_apertura,
            tiempo_analisis,tiempo_atencion,tiempo_reporte,localidad,tiempo_cliente,vobo_sitio,vobo_cliente
        )VALUES (
            %(fecha)s,%(alciti)s,%(seguimiento)s,%(caso_ibm)s,%(caso_citi)s,%(fecha_apertura)s,
            %(severidad)s,%(ingeniero)s,%(serie)s,%(hostname)s,%(ubicacion)s,%(marca)s,%(modelo)s,
            %(fecha_garantia)s,%(caso_proveedor)s,%(falla)s,%(ventana)s,%(status)s,%(tipo_servicio)s,
            %(needpart)s,%(ubicacion_parte)s,%(notas)s,%(status_principal)s,%(marca_csp)s,%(modelo_csp)s,
            %(fecha_alerta)s,%(fecha_solucion)s,%(inicio_analisis)s,%(fin_analisis)s,%(inicio_atencion)s,
            %(fin_atencion)s,%(tiempo_apertura)s,%(tiempo_analisis)s,%(tiempo_atencion)s,%(tiempo_reporte)s,
            %(localidad)s,%(tiempo_cliente)s,%(vobo_sitio)s,%(vobo_cliente)s
        );
            """

        row_db = {
            "alciti": row["ALERTAMIENTO CITI"],
            "seguimiento": row["SEGUIMIENTO CITI"],
            "caso_ibm": row["CASO IBM"],
            "caso_citi": row["CASO CITI"],
            "severidad": row["SEVERIDAD"],
            "ingeniero": row["INGENIERO"],
            "serie": row["SERIE EQUIPO"],
            "hostname": row["HOST NAME"],
            "ubicacion": row["UBICACIÓN"],
            "marca": row["MARCA"],
            "modelo": row["MODELO"],
            "caso_proveedor": row["CASO PROOVEDOR"],
            "falla": row["FALLA"],
            "ventana": row["VENTANA DE SERVICIO"],
            "status": row["STATUS"],
            "tipo_servicio": row["TIPO DE SERVICIO"],
            "needpart": row["SE NECESITA PARTE"],
            "ubicacion_parte": row["UBICACIÓN DE PARTE"],
            "notas": row["NOTAS"],
            "status_principal": row["CASO ABIERTO/CERRADO"],
            "marca_csp": row["MARCA CSP"],
            "modelo_csp": row["MODELO CSP"],
            "tiempo_apertura": parse_int(row["TIEMPO APERTURA"]),
            "tiempo_analisis": parse_int(row["TIEMPO ANALISIS"]),
            "tiempo_atencion": parse_int(row["TIEMPO ATENCION"]),
            "tiempo_reporte": parse_int(row["TIEMPO REPORTE"]),
            "tiempo_cliente": parse_int(row["TIEMPO CLIENTE"]),
            "localidad": row["LOCALIDAD"],
            "vobo_sitio": row["VOBO SITIO"],
            "vobo_cliente": row["VOBO CLIENTE"],
            "fecha": parse_datetime(row["FECHA"]),
            "fecha_apertura": parse_datetime(row["FECHA DE APERTURA"]),
            "fecha_alerta": parse_datetime(row["FECHA ALERTAMIENTO"]),
            "fecha_solucion": parse_datetime(row["FECHA SOLUCION"]),
            "inicio_analisis": parse_datetime(row["FECHA INICIO ANALISIS"]),
            "fin_analisis": parse_datetime(row["FECHA FIN ANALISIS"]),
            "inicio_atencion": parse_datetime(row["INICIO DE ATENCION"]),
            "fin_atencion": parse_datetime(row["FIN DE ATENCION"]),
            "fecha_garantia": parse_datetime(row["FECHA GARANTIA"]),
        }

        cursor.execute(sql, row_db)
conn.commit()
cursor.close()
conn.close()

print("Importación de CASOS finalizada correctamente")
