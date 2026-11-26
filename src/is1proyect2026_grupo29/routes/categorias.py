from flask import Blueprint, jsonify, request

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import Categoria


categorias_bp = Blueprint(
    "categorias",
    __name__,
    url_prefix="/categorias",
)


@categorias_bp.route("/", methods=["GET"])
def listar_categorias():
    session = get_db_session()

    categorias = session.query(Categoria).all()

    resultado = [
        {
            "id": categoria.id,
            "descripcion": categoria.descripcion,
        }
        for categoria in categorias
    ]

    return jsonify(resultado), 200


@categorias_bp.route("/<int:categoria_id>", methods=["GET"])
def obtener_categoria(categoria_id):
    session = get_db_session()

    categoria = session.get(Categoria, categoria_id)

    if categoria is None:
        return jsonify({
            "error": "Categoria no encontrada"
        }), 404

    resultado = {
        "id": categoria.id,
        "descripcion": categoria.descripcion,
    }

    return jsonify(resultado), 200


@categorias_bp.route("/", methods=["POST"])
def crear_categoria():
    session = get_db_session()

    datos = request.get_json()

    if not datos or not datos.get("descripcion"):
        return jsonify({
            "error": "El campo descripcion es obligatorio"
        }), 400

    categoria = Categoria(
        descripcion=datos["descripcion"]
    )

    try:
        session.add(categoria)
        session.commit()

        return jsonify({
            "id": categoria.id,
            "descripcion": categoria.descripcion
        }), 201

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo crear la categoria"
        }), 500


@categorias_bp.route("/<int:categoria_id>", methods=["PUT"])
def actualizar_categoria(categoria_id):
    session = get_db_session()

    categoria = session.get(Categoria, categoria_id)

    if categoria is None:
        return jsonify({
            "error": "Categoria no encontrada"
        }), 404

    datos = request.get_json()

    if not datos or not datos.get("descripcion"):
        return jsonify({
            "error": "El campo descripcion es obligatorio"
        }), 400

    try:
        categoria.descripcion = datos["descripcion"]

        session.commit()

        return jsonify({
            "id": categoria.id,
            "descripcion": categoria.descripcion
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo actualizar la categoria"
        }), 500


@categorias_bp.route("/<int:categoria_id>", methods=["DELETE"])
def eliminar_categoria(categoria_id):
    session = get_db_session()

    categoria = session.get(Categoria, categoria_id)

    if categoria is None:
        return jsonify({
            "error": "Categoria no encontrada"
        }), 404

    try:
        session.delete(categoria)
        session.commit()

        return jsonify({
            "mensaje": "Categoria eliminada correctamente"
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo eliminar la categoria"
        }), 500


