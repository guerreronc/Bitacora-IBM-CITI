from functools import wraps
from flask import session, redirect, url_for, flash

def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login.login_route"))
        return f(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("login.login_route"))

            if user.get("role") not in roles:
                flash("No tienes permisos para acceder a esta sección.", "danger")
                return redirect(url_for("menu.menu"))

            return f(*args, **kwargs)
        return wrapper
    return decorator
