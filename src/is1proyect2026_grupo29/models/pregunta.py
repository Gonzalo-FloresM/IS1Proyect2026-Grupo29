from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from is1proyect2026_grupo29.database.base import Base


class Pregunta(Base):
    """Pregunta creada por un usuario."""

    __tablename__ = "preguntas"

    id: Mapped[int] = mapped_column(primary_key=True)

    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    texto: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relación con Categoria
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id"),
        nullable=False,
    )

    categoria: Mapped["Categoria"] = relationship(
        back_populates="preguntas",
    )

    # Relación con User
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )

    usuario: Mapped["User"] = relationship(
        back_populates="preguntas",
    )
    
    tags: Mapped[list["Tag"]] = relationship(
        secondary="pregunta_tag",
        back_populates="preguntas",
    )
    
    respuestas: Mapped[list["Respuesta"]] = relationship(
        back_populates="pregunta",
    )
