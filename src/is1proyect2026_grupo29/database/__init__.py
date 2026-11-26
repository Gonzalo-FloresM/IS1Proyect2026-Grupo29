from flask import g
from .connection import SessionFactory


def get_db_session():
    """
    Obtiene la sesión de base de datos asociada
    a la petición actual de Flask.
    """
    if "db_session" not in g:
        g.db_session = SessionFactory()

    return g.db_session
