from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from is1proyect2026_grupo29.database.base import Base


class Autor(Base):
    """Clase base abstracta para los autores de respuestas."""

    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30))

    __mapper_args__ = {
        "polymorphic_on": tipo,
        "polymorphic_abstract": True,
    }
    
    respuestas: Mapped[list["Respuesta"]] = relationship(
        back_populates="autor",
    )


class User(Autor):
    """Usuario que puede crear preguntas y responder."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"),
        primary_key=True,
    )
    
    correo_electronico: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    
    contrasena: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    preguntas: Mapped[list["Pregunta"]] = relationship(
        back_populates="usuario",
    )

    __mapper_args__ = {
        "polymorphic_identity": "usuario",
    }


class Admin(User):
    """Usuario administrador."""

    __tablename__ = "administradores"

    id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }


class AgenteIA(Autor):
    """Agente de inteligencia artificial."""

    __tablename__ = "agentes_ia"

    id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"),
        primary_key=True,
    )
    
    estrategia: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    __mapper_args__ = {
        "polymorphic_identity": "agente_ia",
    }
