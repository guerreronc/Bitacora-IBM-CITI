import os

# ============================
#  CONFIGURACIÓN GENERAL
# ============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------
# ARCHIVOS Y CARPETAS
# ----------------------------

# Ruta del archivo principal de Excel
EXCEL_PATH = os.path.join(BASE_DIR, "data", "BITACORA_GENERALIBMCITI.xlsx")

# Archivo JSON de usuarios (para login)
USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")

# Carpeta donde se guardarán logs o adjuntos
UPLOAD_FOLDER = os.path.join(BASE_DIR, "archivos_logs")

# ----------------------------
# FLASK CONFIG
# ----------------------------

# Límite máximo de subida de archivos (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Clave secreta Flask
SECRET_KEY = "clave_super_secreta"


# ============================
#  HOJAS DE EXCEL
# ============================

# Hojas de inventarios KIT por localidad
HOJAS_KIT = {
    "QUERETARO": "KIT DE PARTES QUERETARO",
    "TULTITLAN": "KIT DE PARTES TULTITLAN"
}

# Hoja con catálogo FRU
HOJA_FRU = "PARTES FRU IBM"

# ============================
# HOJAS BASE SERVERS POR LOCALIDAD
# ============================

HOJAS_BASE_SERVERS = {
    "QUERETARO": "BASE_SERVERS",
    "TULTITLAN": "BASE_SERVERS_TULT"
}
