from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from is1proyect2026_grupo29.database.base import Base


class Categoria(Base):
    """Categoría a la que pertenecen las preguntas."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    descripcion: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    preguntas: Mapped[list["Pregunta"]] = relationship(
        back_populates="categoria",
    )
