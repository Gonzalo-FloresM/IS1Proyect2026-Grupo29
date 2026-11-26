from .autor import Autor, User, Admin, AgenteIA
from .categoria import Categoria
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .pregunta import Pregunta
from .tag import Tag
from .respuesta import Respuesta, UserResponse, AgenteIAResponse
from .voto import Voto
