from flask import Blueprint, render_template, request, redirect, url_for, session
from auth import authenticate   # <-- tu función real de login

login_bp = Blueprint("login", __name__)

# ---------------------------
# PANTALLA LOGIN
# ---------------------------
@login_bp.route("/")
def login_route():
    return render_template("login.html")

# ---------------------------
# PROCESO LOGIN
# ---------------------------
@login_bp.route("/login", methods=["POST"])
def login_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = authenticate(username, password)

    if not user:
        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )

    # ---------------------------
    # SESIÓN NORMALIZADA
    # ---------------------------
    session.clear()
    
    session["user"] = user 
    session["user_id"] = user.get("id")
    session["username"] = user.get("username")
    session["name"] = user.get("name")  # <-- CLAVE
    session["role"] = user.get("role")
    session["localidad"] = user.get("localidad", "NO DEFINIDA")

    # ---------------------------
    # CONTROL DE PASSWORD
    # ---------------------------
    session["force_password_change"] = False

    if user.get("role") == "GUEST" and user.get("temp_password"):
        session["force_password_change"] = True
        return redirect(url_for("cambiar_password"))

    return redirect(url_for("menu.menu"))


