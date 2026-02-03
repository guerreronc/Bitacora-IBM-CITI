from flask import Blueprint, render_template, session, redirect, url_for
from flask import jsonify
from datetime import datetime, timedelta
import os

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/menu")
def menu():
    # Verifica si el usuario está logueado
    if "user" not in session:
        return redirect(url_for("login.login_route"))

    # Obtener usuario
    user = session["user"]
    role = user.get("role", "GUEST")
    localidad = session.get("localidad", "NO DEFINIDA")

    # Configuración de menú según rol
    menu_items = []

    if role in ["ADMIN", "ENGINEER"]:
        menu_items = [
            {"name": "Crear Caso", "icon": "📝", "url": "/crear_caso"},
            {"name": "Casos", "icon": "📁", "url": "/casos"},
            {"name": "Historico de Casos", "icon": "📊", "url": url_for("historico_casos.historico_casos")},
            {"name": "Actividades Semanales", "icon": "📅", "url": "/actividades"},
            {"name": "Base Servidores", "icon": "🖥️", "url": url_for("vista_base_servidores")},
            {"name": "Buscar Partes", "icon": "🧩", "url": "/buscar-parte"},
            {"name": "Kit de Partes ", "icon": "🎒", "url": "/kit_partes"},
            {"name": "Consulta de Fallas de Partes", "icon": "📦", "url": url_for("consulta_fallas_partes.resumen_fallas")},
            {"name": "Histórico de Fallas", "icon": "🛠️", "url": "/historico"},
            {"name": "Métricas", "icon": "📈", "url": "/metricas"},
            {"name": "Cargar Archivos", "icon": "📤", "url": "/cargar_archivos"}
        ]

        if role == "ADMIN":
            menu_items.append(
                {"name": "Usuarios", "icon": "👥", "url": "/usuarios"}
            )

    elif role == "GUEST":
        menu_items = [
            {"name": "Histórico de Fallas", "icon": "🛠️", "url": "/historico"},
            {"name": "Historico de Casos", "icon": "📊", "url": url_for("historico_casos.historico_casos")},
            {"name": "Métricas", "icon": "📈", "url": "/metricas"},
            {"name": "Cargar Archivos", "icon": "📤", "url": "/cargar_archivos"}
        ]

    elif role == "ClientCITI":
        menu_items = [
            {"name": "Histórico de Fallas", "icon": "🛠️", "url": "/historico"},
            {"name": "Cargar Archivos", "icon": "📤", "url": "/cargar_archivos"}
        ]

    return render_template(
        "menu.html",
        user=user,
        role=role,
        localidad=localidad,
        menu_items=menu_items
    )
