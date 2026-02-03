import os
import zipfile
import shutil
import tempfile
from flask import Blueprint, current_app, abort, redirect, url_for, flash, session, render_template
from urllib.parse import unquote
from flask import send_from_directory
import xml.etree.ElementTree as ET
from flask import (
    Blueprint, current_app, abort, redirect,
    url_for, flash, session, render_template
)

analizar_bp = Blueprint("analizar_archivos", __name__)


def buscar_viewer_en_zip(zip_path, extract_base):
    """
    Busca viewer.html incluso dentro de ZIPs anidados.
    Devuelve la ruta absoluta del viewer.html o None.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:

        # 1️⃣ Buscar viewer.html directamente
        for zinfo in zip_ref.infolist():
            if zinfo.filename.lower().endswith("viewer.html"):
                zip_ref.extractall(extract_base)
                return os.path.join(extract_base, zinfo.filename)

        # 2️⃣ Buscar ZIPs internos (*.zip)
        for zinfo in zip_ref.infolist():
            if zinfo.filename.lower().endswith(".zip"):

                tmp_dir = tempfile.mkdtemp(dir=extract_base)
                try:
                    zip_ref.extract(zinfo, tmp_dir)
                    inner_zip_path = os.path.join(tmp_dir, zinfo.filename)

                    if os.path.exists(inner_zip_path):
                        result = buscar_viewer_en_zip(inner_zip_path, tmp_dir)
                        if result:
                            return result
                except Exception:
                    pass

    return None

@analizar_bp.route("/viewer/<path:subpath>")
def servir_viewer(subpath):

    if "user" not in session:
        abort(403)

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        abort(403)

    base = os.path.join(current_app.root_path, "temp_viewers")

    return send_from_directory(base, subpath)

@analizar_bp.route("/analizar_zip/<filename>")
def analizar_zip(filename):
    filename = unquote(filename)

    if "user" not in session:
        abort(403)

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        abort(403)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    zip_path = os.path.join(upload_folder, filename)

    print("ARCHIVOS EN DISCO:", os.listdir(upload_folder))
    print("FILENAME RECIBIDO:", filename)

    if not os.path.exists(zip_path):
        abort(404)

    es_zip = filename.lower().endswith(".zip")
    es_xml = filename.lower().endswith(".xml")

    if not es_zip and not es_xml:
        abort(404)

    temp_base = os.path.join(current_app.root_path, "temp_viewers")
    os.makedirs(temp_base, exist_ok=True)

    extract_dir = os.path.join(
        temp_base, os.path.splitext(filename)[0].replace(" ", "_")
    )

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    os.makedirs(extract_dir, exist_ok=True)

    try:
        viewer_fs_path = buscar_viewer_en_zip(zip_path, extract_dir)
    except zipfile.BadZipFile:
        flash("El archivo ZIP está corrupto.", "danger")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    if not viewer_fs_path:
        flash("No se encontró viewer.html dentro del paquete TSR.", "warning")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    rel_path = os.path.relpath(
        viewer_fs_path,
        os.path.join(current_app.root_path, "temp_viewers")
    )

    # 🔥 NORMALIZAR RUTA PARA URL
    rel_path = rel_path.replace("\\", "/")

    return redirect(url_for("analizar_archivos.servir_viewer", subpath=rel_path))

@analizar_bp.route("/analizar_texto/<filename>")
def analizar_texto(filename):

    if "user" not in session:
        abort(403)

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        abort(403)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        abort(404)

    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    if ext not in ["xml", "ahs", "adu"]:
        abort(403)

    try:
        with open(file_path, "r", errors="ignore") as f:
            contenido = f.read()
    except Exception:
        abort(500)

    return render_template(
        "visor_logs.html",
        filename=filename,
        extension=ext,
        contenido=contenido
    )
import csv
from flask import render_template

@analizar_bp.route("/analizar_iml/<filename>")
def analizar_iml(filename):
    filename = unquote(filename)

    if "user" not in session:
        abort(403)

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        abort(403)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path) or not filename.lower().endswith(".csv"):
        abort(404)

    registros = []

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                registros.append({
                    "id": row.get("ID", ""),
                    "severity": row.get("Severity", "").strip(),
                    "class": row.get("Class", ""),
                    "description": row.get("Description", ""),
                    "fecha": row.get("Last Update", ""),
                    "count": row.get("Count", ""),
                    "category": row.get("Category", "")
                })

    except Exception as e:
        flash("Error al leer el archivo IML.", "danger")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    # Ordenar por fecha (string funciona porque viene consistente)
    registros.sort(key=lambda x: x["fecha"], reverse=True)

    return render_template(
        "visor_iml.html",
        registros=registros,
        filename=filename
    )

@analizar_bp.route("/analizar_adu/<filename>")
def analizar_adu(filename):
    filename = unquote(filename)

    # 🔐 Seguridad
    if "user" not in session:
        abort(403)

    role = session["user"]["role"]
    if role not in ["ADMIN", "ENGINEER"]:
        abort(403)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        abort(404)

    ext = filename.lower().rsplit(".", 1)[-1]

    xml_path = None

    # =========================
    # 🟢 CASO 1: XML DIRECTO
    # =========================
    if ext == "xml":
        xml_path = file_path

    # =========================
    # 🟦 CASO 2: ZIP ADU
    # =========================
    elif ext == "zip":
        temp_base = os.path.join(current_app.root_path, "temp_adu")
        os.makedirs(temp_base, exist_ok=True)

        extract_dir = os.path.join(temp_base, os.path.splitext(filename)[0])
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)

        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            for root_dir, _, files in os.walk(extract_dir):
                for f in files:
                    if f.lower() == "adureport.xml":
                        xml_path = os.path.join(root_dir, f)
                        break
        except Exception:
            flash("No fue posible extraer el archivo ADU.", "danger")
            return redirect(url_for("cargar_archivos.cargar_archivos"))

        if not xml_path:
            flash("No se encontró ADUReport.xml dentro del ZIP.", "warning")
            return redirect(url_for("cargar_archivos.cargar_archivos"))

    else:
        flash("Tipo de archivo no compatible para visor ADU.", "warning")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    # =========================
    # 📊 PARSEO XML (MISMO PARA ZIP Y XML)
    # =========================
    registros = []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 🔴 1. Errores reales
        for msg in root.iter():
            if msg.tag.endswith("Message"):
                severity = msg.attrib.get("severity", "").upper()
                if severity in ["CRITICAL", "ERROR", "WARNING"]:
                    registros.append({
                        "fecha": "",
                        "severity": severity,
                        "componente": msg.attrib.get("marketingName", "N/D"),
                        "mensaje": msg.attrib.get("message", "").strip()
                    })

        # 🟠 2. MetaProperty con statusLevel
        for elem in root.iter():
            if elem.tag.endswith("MetaProperty"):
                status = elem.attrib.get("statusLevel", "").upper()
                if status in ["CRITICAL", "ERROR", "WARNING"]:
                    registros.append({
                        "fecha": "",
                        "severity": status,
                        "componente": elem.attrib.get("id", "MetaProperty"),
                        "mensaje": elem.attrib.get("metaValue", elem.attrib.get("value", ""))
                    })

        # 🟡 3. Status textual
        for elem in root.iter():
            if elem.tag.endswith("MetaProperty") and elem.attrib.get("id") == "Status":
                status = elem.attrib.get("value", "").upper()
                if status in ["CRITICAL", "ERROR", "WARNING"]:
                    registros.append({
                        "fecha": "",
                        "severity": status,
                        "componente": "Estado del dispositivo",
                        "mensaje": status
                    })

    except Exception:
        flash("No fue posible interpretar el archivo ADU/XML.", "danger")
        return redirect(url_for("cargar_archivos.cargar_archivos"))

    # =========================
    # 🚿 FILTRO DE RUIDO TÉCNICO
    # =========================
    componentes_ruido = {
        "Command Status",
        "SCSI Status",
        "Sense Key",
        "ASC",
        "ASCQ",
        "Unit Status"
    }

    registros = [
        r for r in registros
        if r.get("componente") not in componentes_ruido
    ]

    return render_template(
        "visor_adu.html",
        filename=filename,
        registros=registros
    )


