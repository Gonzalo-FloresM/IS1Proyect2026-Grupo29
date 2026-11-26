from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from is1proyect2026_grupo29.database import get_db_session
from is1proyect2026_grupo29.models import User, Admin, Pregunta, Voto, Respuesta


usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios",
)

@usuarios_bp.route("/", methods=["POST"])
def crear_usuario():
    session = get_db_session()

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "error": "Se requiere un objeto JSON"
        }), 400

    correo = datos.get("correo_electronico")
    contrasena = datos.get("contrasena")

    if not isinstance(correo, str) or not correo.strip():
        return jsonify({
            "error": "El correo electronico es obligatorio"
        }), 400

    if not isinstance(contrasena, str) or not contrasena:
        return jsonify({
            "error": "La contrasena es obligatoria"
        }), 400

    correo = correo.strip().lower()

    if len(correo) > 255:
        return jsonify({
            "error": "El correo electronico no puede superar los 255 caracteres"
        }), 400

    if len(contrasena) < 8:
        return jsonify({
            "error": "La contrasena debe tener al menos 8 caracteres"
        }), 400

    if len(contrasena) > 1024:
        return jsonify({
            "error": "La contrasena es demasiado larga"
        }), 400

    usuario_existente = session.query(User).filter_by(
        correo_electronico=correo
    ).first()

    if usuario_existente is not None:
        return jsonify({
            "error": "El correo electronico ya esta registrado"
        }), 409

    usuario = User(
        correo_electronico=correo,
        contrasena=generate_password_hash(contrasena),
    )

    try:
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        return jsonify({
            "id": usuario.id,
            "correo_electronico": usuario.correo_electronico,
            "mensaje": "Usuario registrado correctamente"
        }), 201

    except IntegrityError:
        session.rollback()

        return jsonify({
            "error": "El correo electronico ya esta registrado"
        }), 409

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo registrar el usuario"
        }), 500
        
@usuarios_bp.route("/<int:usuario_id>", methods=["GET"])
def obtener_usuario(usuario_id):
    session = get_db_session()

    usuario = session.get(User, usuario_id)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    return jsonify({
        "id": usuario.id,
        "correo_electronico": usuario.correo_electronico,
    }), 200


@usuarios_bp.route("/<int:usuario_id>", methods=["PUT"])
def actualizar_usuario(usuario_id):
    session = get_db_session()

    usuario = session.get(User, usuario_id)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict) or not datos:
        return jsonify({
            "error": "Se requiere un objeto JSON con datos para actualizar"
        }), 400

    if "correo_electronico" in datos:
        correo = datos["correo_electronico"]

        if not isinstance(correo, str) or not correo.strip():
            return jsonify({
                "error": "El correo electronico no es valido"
            }), 400

        correo = correo.strip().lower()

        if len(correo) > 255:
            return jsonify({
                "error": "El correo electronico no puede superar los 255 caracteres"
            }), 400

        usuario_existente = session.query(User).filter(
            User.correo_electronico == correo,
            User.id != usuario_id
        ).first()

        if usuario_existente is not None:
            return jsonify({
                "error": "El correo electronico ya esta registrado"
            }), 409

        usuario.correo_electronico = correo

    if "contrasena" in datos:
        contrasena = datos["contrasena"]

        if not isinstance(contrasena, str) or len(contrasena) < 8:
            return jsonify({
                "error": "La contrasena debe tener al menos 8 caracteres"
            }), 400

        if len(contrasena) > 1024:
            return jsonify({
                "error": "La contrasena es demasiado larga"
            }), 400

        usuario.contrasena = generate_password_hash(contrasena)

    try:
        session.commit()
        session.refresh(usuario)

        return jsonify({
            "id": usuario.id,
            "correo_electronico": usuario.correo_electronico,
            "mensaje": "Usuario actualizado correctamente"
        }), 200

    except IntegrityError:
        session.rollback()

        return jsonify({
            "error": "El correo electronico ya esta registrado"
        }), 409

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo actualizar el usuario"
        }), 500


@usuarios_bp.route("/<int:usuario_id>", methods=["DELETE"])
def eliminar_usuario(usuario_id):
    session = get_db_session()

    usuario = session.get(User, usuario_id)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404
    
    if isinstance(usuario, Admin):
        return jsonify({
            "error": "No se puede eliminar un administrador desde este endpoint"
        }), 403

    tiene_preguntas = session.query(
        session.query(Pregunta.id).filter_by(
            usuario_id=usuario_id
        ).exists()
    ).scalar()

    tiene_votos = session.query(
        session.query(Voto.id).filter_by(
            usuario_id=usuario_id
        ).exists()
    ).scalar()

    tiene_respuestas = session.query(
        session.query(Respuesta.id).filter_by(
            autor_id=usuario_id
        ).exists()
    ).scalar()

    if tiene_preguntas or tiene_votos or tiene_respuestas:
        return jsonify({
            "error": "No se puede eliminar el usuario porque tiene preguntas, votos o respuestas asociadas"
        }), 409

    try:
        session.delete(usuario)
        session.commit()

        return jsonify({
            "mensaje": "Usuario eliminado correctamente"
        }), 200

    except Exception:
        session.rollback()

        return jsonify({
            "error": "No se pudo eliminar el usuario"
        }), 500
