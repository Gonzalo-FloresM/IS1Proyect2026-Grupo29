from flask import Blueprint, jsonify, request

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import Tag


tags_bp = Blueprint(
    "tags",
    __name__,
    url_prefix="/tags",
)


@tags_bp.route("/", methods=["GET"])
def listar_tags():
    session = get_db_session()

    tags = session.query(Tag).order_by(Tag.descripcion).all()

    resultado = [
        {
            "id": tag.id,
            "descripcion": tag.descripcion,
        }
        for tag in tags
    ]

    return jsonify(resultado), 200


@tags_bp.route("/<int:tag_id>", methods=["GET"])
def obtener_tag(tag_id):
    session = get_db_session()

    tag = session.get(Tag, tag_id)

    if tag is None:
        return jsonify({"error": "Tag no encontrado"}), 404

    resultado = {
        "id": tag.id,
        "descripcion": tag.descripcion,
    }

    return jsonify(resultado), 200


@tags_bp.route("/", methods=["POST"])
def crear_tag():
    session = get_db_session()
    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    descripcion = datos.get("descripcion")

    if not isinstance(descripcion, str) or not descripcion.strip():
        return jsonify({"error": "La descripcion es obligatoria"}), 400

    descripcion = descripcion.strip()

    tag_existente = (
        session.query(Tag)
        .filter_by(descripcion=descripcion)
        .first()
    )

    if tag_existente is not None:
        return jsonify({"error": "Ya existe un tag con esa descripcion"}), 409

    tag = Tag(descripcion=descripcion)

    try:
        session.add(tag)
        session.commit()
        session.refresh(tag)

        return jsonify({
            "id": tag.id,
            "descripcion": tag.descripcion,
        }), 201

    except Exception:
        session.rollback()
        return jsonify({"error": "No se pudo crear el tag"}), 500


@tags_bp.route("/<int:tag_id>", methods=["PUT"])
def actualizar_tag(tag_id):
    session = get_db_session()

    tag = session.get(Tag, tag_id)

    if tag is None:
        return jsonify({"error": "Tag no encontrado"}), 404

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    descripcion = datos.get("descripcion")

    if not isinstance(descripcion, str) or not descripcion.strip():
        return jsonify({"error": "La descripcion es obligatoria"}), 400

    descripcion = descripcion.strip()

    tag_existente = (
        session.query(Tag)
        .filter(
            Tag.descripcion == descripcion,
            Tag.id != tag_id,
        )
        .first()
    )

    if tag_existente is not None:
        return jsonify({"error": "Ya existe otro tag con esa descripcion"}), 409

    try:
        tag.descripcion = descripcion
        session.commit()
        session.refresh(tag)

        return jsonify({
            "id": tag.id,
            "descripcion": tag.descripcion,
        }), 200

    except Exception:
        session.rollback()
        return jsonify({"error": "No se pudo actualizar el tag"}), 500


@tags_bp.route("/<int:tag_id>", methods=["DELETE"])
def eliminar_tag(tag_id):
    session = get_db_session()

    tag = session.get(Tag, tag_id)

    if tag is None:
        return jsonify({"error": "Tag no encontrado"}), 404

    try:
        session.delete(tag)
        session.commit()

        return jsonify({
            "mensaje": "Tag eliminado correctamente"
        }), 200

    except Exception:
        session.rollback()
        return jsonify({
            "error": "No se pudo eliminar el tag"
        }), 409

