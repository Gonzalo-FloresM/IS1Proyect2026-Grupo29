from flask import Blueprint, jsonify, request

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import Respuesta, UserResponse, AgenteIAResponse, Pregunta, User, AgenteIA


respuestas_bp = Blueprint(
    "respuestas",
    __name__,
    url_prefix="/respuestas",
)


@respuestas_bp.route("/", methods=["GET"])
def listar_respuestas():
    session = get_db_session()

    respuestas = (
        session.query(Respuesta)
        .order_by(Respuesta.id)
        .all()
    )

    return jsonify([
        {
            "id": respuesta.id,
            "texto": respuesta.texto,
            "aceptada": respuesta.aceptada,
            "tipo": respuesta.tipo,
            "pregunta_id": respuesta.pregunta_id,
            "autor_id": respuesta.autor_id,
            "puntuacion": respuesta.puntuacion,
        }
        for respuesta in respuestas
    ]), 200


@respuestas_bp.route("/<int:respuesta_id>", methods=["GET"])
def obtener_respuesta(respuesta_id):
    session = get_db_session()

    respuesta = session.get(Respuesta, respuesta_id)

    if respuesta is None:
        return jsonify({
            "error": "Respuesta no encontrada"
        }), 404

    return jsonify({
        "id": respuesta.id,
        "texto": respuesta.texto,
        "aceptada": respuesta.aceptada,
        "tipo": respuesta.tipo,
        "pregunta_id": respuesta.pregunta_id,
        "autor_id": respuesta.autor_id,
        "puntuacion": respuesta.puntuacion,
    }), 200
    
@respuestas_bp.route("/", methods=["POST"])
def crear_respuesta():
    session = get_db_session()

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "Se requiere un cuerpo JSON"
        }), 400

    texto = datos.get("texto")
    pregunta_id = datos.get("pregunta_id")
    autor_id = datos.get("autor_id")
    tipo = datos.get("tipo")

    if not isinstance(texto, str) or not texto.strip():
        return jsonify({
            "error": "El texto es obligatorio"
        }), 400

    if not isinstance(pregunta_id, int) or isinstance(pregunta_id, bool):
        return jsonify({
            "error": "pregunta_id debe ser un entero"
        }), 400

    if not isinstance(autor_id, int) or isinstance(autor_id, bool):
        return jsonify({
            "error": "autor_id debe ser un entero"
        }), 400

    if tipo not in ("usuario", "agente_ia"):
        return jsonify({
            "error": "El tipo debe ser 'usuario' o 'agente_ia'"
        }), 400

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({
            "error": "Pregunta no encontrada"
        }), 404

    if tipo == "usuario":
        autor = session.get(User, autor_id)
        clase_respuesta = UserResponse
    else:
        autor = session.get(AgenteIA, autor_id)
        clase_respuesta = AgenteIAResponse

    if autor is None:
        return jsonify({
            "error": "Autor no encontrado o incompatible con el tipo indicado"
        }), 404

    respuesta = clase_respuesta(
        texto=texto.strip(),
        pregunta_id=pregunta_id,
        autor_id=autor_id,
    )

    try:
        session.add(respuesta)
        session.commit()
        session.refresh(respuesta)

        return jsonify({
            "id": respuesta.id,
            "texto": respuesta.texto,
            "aceptada": respuesta.aceptada,
            "tipo": respuesta.tipo,
            "pregunta_id": respuesta.pregunta_id,
            "autor_id": respuesta.autor_id,
            "puntuacion": respuesta.puntuacion,
        }), 201

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo crear la respuesta"
        }), 500
        
@respuestas_bp.route("/<int:respuesta_id>", methods=["PUT"])
def actualizar_respuesta(respuesta_id):
    session = get_db_session()

    respuesta = session.get(Respuesta, respuesta_id)

    if respuesta is None:
        return jsonify({
            "error": "Respuesta no encontrada"
        }), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "error": "Se requiere un cuerpo JSON"
        }), 400

    if "texto" in datos:
        texto = datos["texto"]

        if not isinstance(texto, str) or not texto.strip():
            return jsonify({
                "error": "El texto no puede estar vacío"
            }), 400

        respuesta.texto = texto.strip()

    if "aceptada" in datos:
        aceptada = datos["aceptada"]

        if not isinstance(aceptada, bool):
            return jsonify({
                "error": "aceptada debe ser un valor booleano"
            }), 400

        respuesta.aceptada = aceptada

    try:
        session.commit()
        session.refresh(respuesta)

        return jsonify({
            "id": respuesta.id,
            "texto": respuesta.texto,
            "aceptada": respuesta.aceptada,
            "tipo": respuesta.tipo,
            "pregunta_id": respuesta.pregunta_id,
            "autor_id": respuesta.autor_id,
            "puntuacion": respuesta.puntuacion,
        }), 200

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo actualizar la respuesta"
        }), 500
        
@respuestas_bp.route("/<int:respuesta_id>", methods=["DELETE"])
def eliminar_respuesta(respuesta_id):
    session = get_db_session()

    respuesta = session.get(Respuesta, respuesta_id)

    if respuesta is None:
        return jsonify({
            "error": "Respuesta no encontrada"
        }), 404

    try:
        session.delete(respuesta)
        session.commit()

        return jsonify({
            "mensaje": "Respuesta eliminada correctamente"
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo eliminar la respuesta. Puede tener votos asociados."
        }), 409