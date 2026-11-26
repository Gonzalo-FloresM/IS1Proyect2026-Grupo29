
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar las variables del archivo .env
load_dotenv()

# Obtener la URL de conexión
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "No se encontró la variable de entorno DATABASE_URL"
    )

# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Crear la fábrica de sesiones
SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
