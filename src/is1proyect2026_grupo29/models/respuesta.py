from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from is1proyect2026_grupo29.database.base import Base


class Respuesta(Base):
    """Clase base para las respuestas."""

    __tablename__ = "respuestas"

    id: Mapped[int] = mapped_column(primary_key=True)

    texto: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    aceptada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    """Calcula la puntuación sumando los votos recibidos."""
    @property
    def puntuacion(self) -> int:
        return sum(voto.valor for voto in self.votos)
    
    tipo: Mapped[str] = mapped_column(String(30))

    pregunta_id: Mapped[int] = mapped_column(
        ForeignKey("preguntas.id"),
        nullable=False,
    )

    autor_id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"),
        nullable=False,
    )

    pregunta: Mapped["Pregunta"] = relationship(
        back_populates="respuestas",
    )

    autor: Mapped["Autor"] = relationship(
        back_populates="respuestas",
    )
    
    votos: Mapped[list["Voto"]] = relationship(
        back_populates="respuesta",
    )

    __mapper_args__ = {
        "polymorphic_on": tipo,
        "polymorphic_abstract": True,
    }


class UserResponse(Respuesta):
    """Respuesta generada por un usuario."""

    __tablename__ = "respuestas_usuario"

    id: Mapped[int] = mapped_column(
        ForeignKey("respuestas.id"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "usuario",
    }


class AgenteIAResponse(Respuesta):
    """Respuesta generada por un agente de IA."""

    __tablename__ = "respuestas_agente_ia"

    id: Mapped[int] = mapped_column(
        ForeignKey("respuestas.id"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "agente_ia",
    }
