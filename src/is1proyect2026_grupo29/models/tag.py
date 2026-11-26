from sqlalchemy import String, Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from is1proyect2026_grupo29.database.base import Base


pregunta_tag = Table(
    "pregunta_tag",
    Base.metadata,
    Column(
        "pregunta_id",
        ForeignKey("preguntas.id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id"),
        primary_key=True,
    ),
)


class Tag(Base):
    """Etiqueta que permite clasificar preguntas."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)

    descripcion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    preguntas: Mapped[list["Pregunta"]] = relationship(
        secondary="pregunta_tag",
        back_populates="tags",
    )
