from config import SECRET_KEY, FLASK_DEBUG
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from datetime import datetime
import os
from modules.users_repository import (
    get_user_by_username,
    update_user
)
from modules.users_repository import delete_user
from modules.security import require_login, require_role
from modules.crear_caso import register_crear_caso
from modules.casos_routes import casos_bp
from modules.registrar_parte import registrar_parte_bp
from modules.mensajeria_routes import mensajeria_bp
from modules.historico_casos import historico_casos_bp
from modules.actividades_semanales import actividades_bp
from modules.base_servidores import base_servidores_bp
from modules.buscar_parte import buscar_parte_bp
from modules.kit_partes import kit_bp  # importamos el blueprint
from modules.consulta_fallas_partes import consulta_fallas_partes_bp
from modules.historico_fallas import historico_fallas_bp
from modules.metricas_routes import metricas_bp
from modules.cargar_archivos import cargar_archivos_bp
from modules.analizar_archivos import analizar_bp
from modules.login_routes import login_bp
from db import get_connection
from modules.menu_routes import menu_bp
from helpers.alertas import obtener_alertas
from dotenv import load_dotenv

load_dotenv()

def to_dt(valor):
    """Convierte string ISO (YYYY-MM-DDTHH:MM) a datetime, devuelve None si está vacío o inválido"""
    try:
        return datetime.fromisoformat(valor) if valor else None
    except:
        return None

def icono_archivo(filename):
    ext = filename.split(".")[-1].lower()
    if ext in ["xls", "xlsx"]:
        return "📊"   # Excel
    elif ext in ["rar", "zip"]:
        return "🗜️"   # Comprimidos
    elif ext in ["adu"]:
        return "💾"   # ADU o binarios
    elif ext in ["txt", "log"]:
        return "📄"   # Texto/Logs
    elif ext in ["pdf"]:
        return "📕"
    else:
        return "📁"   # Otros
# -------------------------
# FUNCIONES AUXILIARES
# -------------------------
    
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "archivos_logs")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB máximo por archivo
app.secret_key = SECRET_KEY
app.debug = FLASK_DEBUG
register_crear_caso(app)
app.register_blueprint(casos_bp)
app.register_blueprint(registrar_parte_bp)
app.register_blueprint(mensajeria_bp)
app.register_blueprint(historico_casos_bp)
app.register_blueprint(actividades_bp, url_prefix="/actividades")
app.register_blueprint(base_servidores_bp)
app.register_blueprint(buscar_parte_bp)
app.register_blueprint(kit_bp)
app.register_blueprint(consulta_fallas_partes_bp)
app.register_blueprint(historico_fallas_bp)
app.register_blueprint(metricas_bp)
app.register_blueprint(cargar_archivos_bp)
app.register_blueprint(analizar_bp)
app.register_blueprint(login_bp)
app.register_blueprint(menu_bp)

@app.before_request
def validar_sesion():
    # Rutas públicas
    rutas_publicas = [
        "login.login_route",
        "login.login_process",
        "logout",
        "cambiar_password"
    ]

    # Archivos estáticos
    if request.endpoint == "static":
        return

    # Endpoint puede ser None (errores 404, etc.)
    if request.endpoint is None:
        return

    # Permitir rutas públicas
    if request.endpoint in rutas_publicas:
        return

    # Validar sesión
    if "user" not in session:
        return redirect(url_for("login.login_route"))

@app.route("/cambiar_password", methods=["GET", "POST"])
def cambiar_password():

    # Sesión ya validada por before_request
    current_user = session["user"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, password, temp_password, role, localidad, name, email, activo
        FROM usuarios
        WHERE username = %s
    """, (current_user["username"],))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("login.login_route"))

    # ---------- GET ----------
    if request.method == "GET":
        cursor.close()
        conn.close()
        return render_template("cambiar_password.html", usuario=usuario)

    # ---------- POST ----------
    actual = request.form.get("current_password", "").strip()
    nueva = request.form.get("new_password", "").strip()
    confirmar = request.form.get("confirm_password", "").strip()

    if not nueva or nueva != confirmar:
        flash("Las contraseñas nuevas no coinciden o están vacías.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("cambiar_password"))

    if not usuario["temp_password"] and actual != usuario["password"]:
        flash("La contraseña actual es incorrecta.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("cambiar_password"))

    cursor.execute("""
        UPDATE usuarios
        SET password = %s, temp_password = 0
        WHERE username = %s
    """, (nueva, usuario["username"]))
    conn.commit()

    # 🔁 Recargar usuario actualizado
    cursor.execute("""
        SELECT username, role, localidad, temp_password, name, email, activo
        FROM usuarios
        WHERE username = %s
    """, (usuario["username"],))
    usuario_actualizado = cursor.fetchone()

    cursor.close()
    conn.close()

    session["user"] = usuario_actualizado

    flash("Contraseña actualizada correctamente.", "success")
    return redirect(url_for("menu.menu"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login.login_route"))

# ==========================
# USUARIOS - CRUD
# ==========================
# Listar usuarios y crear/editar desde el mismo template
@app.route("/usuarios", methods=["GET", "POST"])
@require_login
@require_role("ADMIN")
def usuarios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    mensaje = None

    if request.method == "POST":
        form = request.form
        name = form.get("name").strip()
        email = form.get("email").strip()
        username = form.get("username").strip()
        password = form.get("password").strip()
        localidad = form.get("localidad").strip()
        role = form.get("role")

        cursor.execute(
            "SELECT 1 FROM usuarios WHERE username = %s",
            (username,)
        )
        if cursor.fetchone():
            mensaje = {"tipo": "danger", "texto": f"El username {username} ya existe."}
        else:
            cursor.execute("""
                INSERT INTO usuarios
                (name, email, username, password, localidad, role, temp_password, activo)
                VALUES (%s, %s, %s, %s, %s, %s, 1, 1)
            """, (name, email, username, password, localidad, role))
            conn.commit()
            mensaje = {"tipo": "success", "texto": f"Usuario {username} creado correctamente."}

    cursor.execute("""
        SELECT name, email, username, role, localidad, activo
        FROM usuarios
        ORDER BY username
    """)
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "Usuarios.html",
        usuarios=usuarios,
        usuario=None,
        mensaje=mensaje
    )
    
# Editar usuario
@app.route("/editar_usuario/<username>", methods=["GET", "POST"])
def editar_usuario(username):

    if session["user"]["role"] != "ADMIN":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu.menu"))

    usuario = get_user_by_username(username)

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("usuarios"))

    if request.method == "POST":
        form = request.form
        password = form.get("password", "").strip()

        data = {
            "name": form.get("name"),
            "email": form.get("email"),
            "localidad": form.get("localidad"),
            "role": form.get("role")
        }

        update_user(username, data, password if password else None)

        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for("usuarios"))

    return render_template("Usuarios.html", usuarios=[], usuario=usuario)

# Eliminar usuario
@app.route("/eliminar_usuario/<username>", methods=["POST"])
def eliminar_usuario(username):

    if session["user"]["role"] != "ADMIN":
        if username == session["user"]["username"]:
            flash("No puedes eliminar tu propio usuario.", "danger")
            return redirect(url_for("usuarios"))
        flash("No tienes permisos.", "danger")
        return redirect(url_for("menu.menu"))

    delete_user(username)

    flash(f"Usuario {username} eliminado correctamente.", "success")
    return redirect(url_for("usuarios"))

# ----------------------
# SELECCIÓN LOCALIDAD
# ----------------------
@app.route("/localidad", methods=["GET", "POST"])
def elegir_localidad():
    # Se asume sesión válida (before_request ya lo garantiza)
    
    if request.method == "POST":
        localidad = request.form.get("localidad", "").strip()
        if localidad:
            session["localidad"] = localidad
            flash(f"Localidad seleccionada: {localidad}", "success")
        else:
            flash("Debe seleccionar una localidad válida.", "danger")
        return redirect(url_for("menu.menu"))
    
    return render_template("localidad.html")

from helpers.alertas import obtener_alertas

@app.context_processor
def inject_user():
    user = session.get("user", {})
        
    alertas = []
    if user:
        try:
            alertas = obtener_alertas({
                "name": user.get("name") or user.get("username"),
                "role": user.get("role"),
                "localidad": session.get("localidad")
            })
        except Exception as e:
            print("Error obteniendo alertas:", e)
            alertas = []

    return {
        "current_user": user.get("name") or user.get("username", "N/D"),
        "current_role": user.get("role", "N/D"),
        "current_localidad": session.get("localidad", "N/D"),
        "usuario": user.get("name") or user.get("username", "N/D"),
        "rol": user.get("role", "N/D"),
        "localidad": session.get("localidad", "N/D"),

        # 🔔 ALERTAS GLOBALES
        "alertas": alertas,
        "total_alertas": len(alertas)
    }

@app.route("/base-servidores")
def vista_base_servidores():
    return render_template("base_servidores.html")

@app.route("/api/alertas")
def api_alertas():
    user = session.get("user")
    if not user:
        return jsonify([])

    localidad = user.get("localidad") or session.get("localidad")
    if not localidad:
        return jsonify([])

    try:
        alertas = obtener_alertas({
            "name": user.get("name") or user.get("username"),
            "role": user.get("role"),
            "localidad": localidad
        })
        return jsonify(alertas)
    except Exception as e:
        print("Error API alertas:", e)
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)
