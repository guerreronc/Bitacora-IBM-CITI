# modules/utils_users.py
from flask import session, abort


def get_current_user():
    user = session.get("user")
    if not user:
        abort(401)
    return user


def get_current_role():
    return session.get("role", "GUEST")


def get_current_localidad():
    return session.get("localidad", "NO DEFINIDA")


def require_role(role):
    if get_current_role() != role:
        abort(403)


def require_any_role(*roles):
    if get_current_role() not in roles:
        abort(403)
