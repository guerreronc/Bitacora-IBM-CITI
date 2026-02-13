import os

# ============================
#  CONFIGURACIÓN GENERAL
# ============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------
# ARCHIVOS Y CARPETAS
# ----------------------------

# Archivo JSON de usuarios (para login)
USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")

# Carpeta donde se guardarán logs o adjuntos
UPLOAD_FOLDER = os.path.join(BASE_DIR, "archivos_logs")

# ----------------------------
# FLASK CONFIG
# ----------------------------

# Límite máximo de subida de archivos (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

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
# ============================
#  CONFIGURACIÓN BASE DE DATOS
# ============================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bitacora_ibm")

# ============================
#  SEGURIDAD / FLASK
# ============================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY no configurada en entorno")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
