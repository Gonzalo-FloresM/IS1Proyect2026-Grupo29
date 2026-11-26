from flask import Blueprint, jsonify, request

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import Pregunta, Categoria, User, Tag


preguntas_bp = Blueprint(
    "preguntas",
    __name__,
    url_prefix="/preguntas",
)


@preguntas_bp.route("/", methods=["GET"])
def listar_preguntas():
    session = get_db_session()

    preguntas = session.query(Pregunta).all()

    resultado = [
        {
            "id": pregunta.id,
            "titulo": pregunta.titulo,
            "texto": pregunta.texto,
            "fecha": pregunta.fecha.isoformat(),
            "categoria_id": pregunta.categoria_id,
            "usuario_id": pregunta.usuario_id,
        }
        for pregunta in preguntas
    ]

    return jsonify(resultado), 200


@preguntas_bp.route("/<int:pregunta_id>", methods=["GET"])
def obtener_pregunta(pregunta_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    resultado = {
        "id": pregunta.id,
        "titulo": pregunta.titulo,
        "texto": pregunta.texto,
        "fecha": pregunta.fecha.isoformat(),
        "categoria_id": pregunta.categoria_id,
        "usuario_id": pregunta.usuario_id,
    }

    return jsonify(resultado), 200


@preguntas_bp.route("/", methods=["POST"])
def crear_pregunta():
    session = get_db_session()
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    titulo = datos.get("titulo")
    texto = datos.get("texto")
    categoria_id = datos.get("categoria_id")
    usuario_id = datos.get("usuario_id")

    if not isinstance(titulo, str) or not titulo.strip():
        return jsonify({"error": "El titulo es obligatorio"}), 400

    if not isinstance(texto, str) or not texto.strip():
        return jsonify({"error": "El texto es obligatorio"}), 400

    if not isinstance(categoria_id, int) or isinstance(categoria_id, bool):
        return jsonify({"error": "El categoria_id debe ser un entero"}), 400

    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        return jsonify({"error": "El usuario_id debe ser un entero"}), 400

    categoria = session.get(Categoria, categoria_id)
    if categoria is None:
        return jsonify({"error": "La categoria no existe"}), 404

    usuario = session.get(User, usuario_id)
    if usuario is None:
        return jsonify({"error": "El usuario no existe"}), 404

    pregunta = Pregunta(
        titulo=titulo.strip(),
        texto=texto.strip(),
        categoria=categoria,
        usuario=usuario,
    )

    try:
        session.add(pregunta)
        session.commit()
        session.refresh(pregunta)

        resultado = {
            "id": pregunta.id,
            "titulo": pregunta.titulo,
            "texto": pregunta.texto,
            "fecha": pregunta.fecha.isoformat(),
            "categoria_id": pregunta.categoria_id,
            "usuario_id": pregunta.usuario_id,
        }

        return jsonify(resultado), 201

    except Exception:
        session.rollback()
        return jsonify({"error": "No se pudo crear la pregunta"}), 500


@preguntas_bp.route("/<int:pregunta_id>", methods=["PUT"])
def actualizar_pregunta(pregunta_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    if "titulo" in datos:
        titulo = datos["titulo"]

        if not isinstance(titulo, str) or not titulo.strip():
            return jsonify({"error": "El titulo no puede estar vacio"}), 400

        pregunta.titulo = titulo.strip()

    if "texto" in datos:
        texto = datos["texto"]

        if not isinstance(texto, str) or not texto.strip():
            return jsonify({"error": "El texto no puede estar vacio"}), 400

        pregunta.texto = texto.strip()

    if "categoria_id" in datos:
        categoria_id = datos["categoria_id"]

        if not isinstance(categoria_id, int) or isinstance(categoria_id, bool):
            return jsonify({"error": "El categoria_id debe ser un entero"}), 400

        categoria = session.get(Categoria, categoria_id)

        if categoria is None:
            return jsonify({"error": "La categoria no existe"}), 404

        pregunta.categoria = categoria

    try:
        session.commit()
        session.refresh(pregunta)

        resultado = {
            "id": pregunta.id,
            "titulo": pregunta.titulo,
            "texto": pregunta.texto,
            "fecha": pregunta.fecha.isoformat(),
            "categoria_id": pregunta.categoria_id,
            "usuario_id": pregunta.usuario_id,
        }

        return jsonify(resultado), 200

    except Exception:
        session.rollback()
        return jsonify({"error": "No se pudo actualizar la pregunta"}), 500


@preguntas_bp.route("/<int:pregunta_id>", methods=["DELETE"])
def eliminar_pregunta(pregunta_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    try:
        session.delete(pregunta)
        session.commit()

        return jsonify({
            "mensaje": "Pregunta eliminada correctamente"
        }), 200

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo eliminar la pregunta. Puede tener respuestas asociadas."
        }), 409


@preguntas_bp.route("/<int:pregunta_id>/tags", methods=["GET"])
def listar_tags_pregunta(pregunta_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    resultado = [
        {
            "id": tag.id,
            "descripcion": tag.descripcion,
        }
        for tag in pregunta.tags
    ]

    return jsonify(resultado), 200



@preguntas_bp.route("/<int:pregunta_id>/tags", methods=["POST"])
def asociar_tag(pregunta_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    tag_id = datos.get("tag_id")

    if not isinstance(tag_id, int) or isinstance(tag_id, bool):
        return jsonify({"error": "El tag_id debe ser un entero"}), 400

    tag = session.get(Tag, tag_id)

    if tag is None:
        return jsonify({"error": "Tag no encontrado"}), 404

    if tag in pregunta.tags:
        return jsonify({"error": "El tag ya esta asociado a esta pregunta"}), 409

    try:
        pregunta.tags.append(tag)
        session.commit()

        return jsonify({
            "mensaje": "Tag asociado correctamente",
            "pregunta_id": pregunta.id,
            "tag_id": tag.id,
        }), 201

    except Exception:
        session.rollback()
        return jsonify({"error": "No se pudo asociar el tag"}), 500


@preguntas_bp.route(
    "/<int:pregunta_id>/tags/<int:tag_id>",
    methods=["DELETE"]
)
def desasociar_tag(pregunta_id, tag_id):
    session = get_db_session()

    pregunta = session.get(Pregunta, pregunta_id)

    if pregunta is None:
        return jsonify({"error": "Pregunta no encontrada"}), 404

    tag = session.get(Tag, tag_id)

    if tag is None:
        return jsonify({"error": "Tag no encontrado"}), 404

    if tag not in pregunta.tags:
        return jsonify({
            "error": "El tag no esta asociado a esta pregunta"
        }), 404

    try:
        pregunta.tags.remove(tag)
        session.commit()

        return jsonify({
            "mensaje": "Tag desasociado correctamente",
            "pregunta_id": pregunta.id,
            "tag_id": tag.id,
        }), 200

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo desasociar el tag"
        }), 500
