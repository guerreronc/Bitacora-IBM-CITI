# modules/cargar_archivos.py

import os
from flask import (
    Blueprint, app, render_template, request, redirect,
    url_for, flash, session, send_from_directory, current_app
)
from datetime import datetime
from werkzeug.utils import secure_filename

cargar_archivos_bp = Blueprint("cargar_archivos", __name__)

# Extensiones permitidas (incluye HPE logs)
ALLOWED_EXTENSIONS = {
    "zip", "rar",
    "png", "jpg", "jpeg",
    "xls", "xlsx",
    "pdf",
    "adu", "ahs",
    "xml","csv"
}

def extension_permitida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def formatear_tamaño(bytes_size):
    for unidad in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unidad}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"

def icono_archivo(nombre):
    ext = nombre.rsplit(".", 1)[-1].lower()
    iconos = {
        "zip": "📦", "rar": "📦",
        "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️",
        "xls": "📊", "xlsx": "📊",
        "pdf": "📄",
        "adu": "🧾", "ahs": "🧾",
        "csv": "🧩"
    }
    return iconos.get(ext, "📁")

def detectar_tipo_archivo(nombre):
    ext = nombre.rsplit(".", 1)[-1].lower()

    if ext in ["zip", "rar"]:
        return "ZIP"

    if ext in ["png", "jpg", "jpeg"]:
        return "IMAGEN"

    if ext in ["xls", "xlsx"]:
        return "EXCEL"

    if ext == "pdf":
        return "PDF"

    if ext in ["adu", "ahs"]:
        return "HPE_LOG"
    
    if ext == "xml":
        return "XML"
    
    if ext == "csv":
        return "CSV"

    return "DESCONOCIDO"

def es_zip_real(filepath):
    try:
        with open(filepath, "rb") as f:
            signature = f.read(4)
            return signature.startswith(b"PK")
    except:
        return False
    
def detectar_estructura_real(filepath):
    """
    Detecta la estructura real del archivo usando magic bytes.
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)

        # ZIP: PK\x03\x04
        if header.startswith(b"PK\x03\x04"):
            return "ZIP"

        # Texto plano (ASCII / UTF-8 simple)
        try:
            header.decode("utf-8")
            return "TEXTO"
        except UnicodeDecodeError:
            pass

        return "BINARIO"

    except Exception:
        return "DESCONOCIDO"

# ===============================
# CARGAR / LISTAR ARCHIVOS
# ===============================
@cargar_archivos_bp.route("/cargar_archivos", methods=["GET", "POST"])
def cargar_archivos():

    if "user" not in session:
        return redirect(url_for("login_route"))

    role = session["user"]["role"]
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    if request.method == "POST":
        if "archivo" not in request.files:
            flash("No se seleccionó archivo", "warning")
        else:
            file = request.files["archivo"]

            if file.filename == "":
                flash("Nombre de archivo inválido", "warning")
                return redirect(url_for("cargar_archivos.cargar_archivos"))


            elif not extension_permitida(file.filename):
                flash("Tipo de archivo no permitido", "danger")

            else:
                filename = os.path.basename(file.filename)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                flash(f"Archivo '{filename}' subido correctamente.", "success")

        return redirect(url_for("cargar_archivos.cargar_archivos"))
   
    archivos = []

    for f in os.listdir(current_app.config["UPLOAD_FOLDER"]):
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], f)

        if os.path.isfile(filepath):
            nombre, extension = os.path.splitext(f)
            extension = extension.lower().replace(".", "")

            size_bytes = os.path.getsize(filepath)
            size_mb = round(size_bytes / (1024 * 1024), 2)

            fecha = datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).strftime("%Y-%m-%d %H:%M")

            archivos.append({
                "nombre": f,              # 🔥 ESTE ES EL REAL
                "extension": extension,
                "icono": icono_archivo(f),
                "tamano": f"{size_mb} MB",
                "fecha": fecha
        })
    
        
    return render_template(
        "cargar_archivos.html",
        archivos=archivos,
        role=role
    )


# ===============================
# DESCARGAR ARCHIVO
# ===============================
@cargar_archivos_bp.route("/descargar_archivo/<filename>")
def descargar_archivo(filename):

    if "user" not in session:
        return redirect(url_for("login_route"))

    safe_filename = os.path.basename(filename)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        safe_filename,
        as_attachment=True
    )


# ===============================
# ELIMINAR ARCHIVO
# ===============================
@cargar_archivos_bp.route("/eliminar_archivo/<filename>")
def eliminar_archivo(filename):

    if "user" not in session:
        return redirect(url_for("login_route"))

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        flash("No tienes permisos para eliminar archivos.", "danger")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Archivo '{filename}' eliminado correctamente.", "success")
    else:
        flash("Archivo no encontrado.", "warning")

    return redirect(url_for("cargar_archivos.cargar_archivos"))
