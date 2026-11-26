from flask import Flask, g
from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.routes.categorias import categorias_bp
from sqlalchemy import text


def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(categorias_bp)

    @app.teardown_appcontext
    def close_db_session(exception=None):
        session = g.pop("db_session", None)
    
        if session is not None:
            if exception is not None:
                session.rollback()
    
            session.close()
    
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "ok"}, 200
    
    @app.route("/health/db", methods=["GET"])
    def database_health_check():
        session = get_db_session()

        session.execute(text("SELECT 1"))

        return {"database": "connected"}, 200

    return app
