from flask import Blueprint, jsonify, request

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import Voto, User, Respuesta


votos_bp = Blueprint(
    "votos",
    __name__,
    url_prefix="/votos",
)


@votos_bp.route("/", methods=["GET"])
def listar_votos():
    session = get_db_session()

    votos = (
        session.query(Voto)
        .order_by(Voto.id)
        .all()
    )

    return jsonify([
        {
            "id": voto.id,
            "usuario_id": voto.usuario_id,
            "respuesta_id": voto.respuesta_id,
            "valor": voto.valor,
            "fecha": voto.fecha.isoformat(),
        }
        for voto in votos
    ]), 200


@votos_bp.route("/<int:voto_id>", methods=["GET"])
def obtener_voto(voto_id):
    session = get_db_session()

    voto = session.get(Voto, voto_id)

    if voto is None:
        return jsonify({
            "error": "Voto no encontrado"
        }), 404

    return jsonify({
        "id": voto.id,
        "usuario_id": voto.usuario_id,
        "respuesta_id": voto.respuesta_id,
        "valor": voto.valor,
        "fecha": voto.fecha.isoformat(),
    }), 200
    
@votos_bp.route("/", methods=["POST"])
def crear_voto():
    session = get_db_session()

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "Se requiere un cuerpo JSON"
        }), 400

    usuario_id = datos.get("usuario_id")
    respuesta_id = datos.get("respuesta_id")
    valor = datos.get("valor")

    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        return jsonify({
            "error": "usuario_id debe ser un entero"
        }), 400

    if not isinstance(respuesta_id, int) or isinstance(respuesta_id, bool):
        return jsonify({
            "error": "respuesta_id debe ser un entero"
        }), 400

    if not isinstance(valor, int) or isinstance(valor, bool) or valor not in (-1, 1):
        return jsonify({
            "error": "El valor del voto debe ser 1 o -1"
        }), 400

    usuario = session.get(User, usuario_id)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    respuesta = session.get(Respuesta, respuesta_id)

    if respuesta is None:
        return jsonify({
            "error": "Respuesta no encontrada"
        }), 404

    voto_existente = session.query(Voto).filter_by(
        usuario_id=usuario_id,
        respuesta_id=respuesta_id,
    ).first()

    if voto_existente is not None:
        return jsonify({
            "error": "El usuario ya voto esta respuesta"
        }), 409

    voto = Voto(
        usuario_id=usuario_id,
        respuesta_id=respuesta_id,
        valor=valor,
    )

    try:
        session.add(voto)
        session.commit()
        session.refresh(voto)

        return jsonify({
            "id": voto.id,
            "usuario_id": voto.usuario_id,
            "respuesta_id": voto.respuesta_id,
            "valor": voto.valor,
            "fecha": voto.fecha.isoformat(),
        }), 201

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo registrar el voto"
        }), 500
        
@votos_bp.route("/<int:voto_id>", methods=["PUT"])
def actualizar_voto(voto_id):
    session = get_db_session()

    voto = session.get(Voto, voto_id)

    if voto is None:
        return jsonify({
            "error": "Voto no encontrado"
        }), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "Se requiere un cuerpo JSON"
        }), 400

    valor = datos.get("valor")

    if not isinstance(valor, int) or isinstance(valor, bool) or valor not in (-1, 1):
        return jsonify({
            "error": "El valor del voto debe ser 1 o -1"
        }), 400

    try:
        voto.valor = valor

        session.commit()
        session.refresh(voto)

        return jsonify({
            "id": voto.id,
            "usuario_id": voto.usuario_id,
            "respuesta_id": voto.respuesta_id,
            "valor": voto.valor,
            "fecha": voto.fecha.isoformat(),
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo actualizar el voto"
        }), 500

@votos_bp.route("/<int:voto_id>", methods=["DELETE"])
def eliminar_voto(voto_id):
    session = get_db_session()

    voto = session.get(Voto, voto_id)

    if voto is None:
        return jsonify({
            "error": "Voto no encontrado"
        }), 404

    try:
        session.delete(voto)
        session.commit()

        return jsonify({
            "mensaje": "Voto eliminado correctamente"
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo eliminar el voto"
        }), 500