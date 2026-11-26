from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from is1proyect2026_grupo29.database.base import Base


class Voto(Base):
    """Voto de un usuario sobre una respuesta."""

    __tablename__ = "votos"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )

    respuesta_id: Mapped[int] = mapped_column(
        ForeignKey("respuestas.id"),
        nullable=False,
    )

    valor: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    usuario: Mapped["User"] = relationship(
        back_populates="votos",
    )

    respuesta: Mapped["Respuesta"] = relationship(
        back_populates="votos",
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "respuesta_id",
            name="uq_voto_usuario_respuesta",
        ),
        CheckConstraint(
            "valor IN (-1, 1)",
            name="ck_voto_valor",
        ),
    )
