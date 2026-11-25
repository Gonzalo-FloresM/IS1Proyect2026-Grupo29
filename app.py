from abc import ABC, abstractmethod
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================================================================
# 1. CONFIGURACIÓN DE FLASK Y BASE DE DATOS
# ==============================================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "clave-secreta-actividad-1"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///foro_ia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================================================================
# 2. PATRÓN STRATEGY (Para AgenteIA)
# ==============================================================================
class IAStrategy(ABC):
    @abstractmethod
    def generar_contenido(self, prompt: str) -> str:
        pass

    @abstractmethod
    def generar_agente(self) -> dict:
        pass


class OpenAIStrategy(IAStrategy):
    def __init__(self, model_name: str = "gpt-4o", api_key: str = "sk-demo"):
        self.model_name = model_name
        self.api_key = api_key

    def generar_agente(self) -> dict:
        return {"proveedor": "OpenAI", "modelo": self.model_name}

    def generar_contenido(self, prompt: str) -> str:
        return f"[OpenAI - {self.model_name}] Respuesta generada para: '{prompt}'"


class GeminiStrategy(IAStrategy):
    def __init__(self, model_name: str = "gemini-2.5-pro", api_key: str = "AIza-demo"):
        self.model_name = model_name
        self.api_key = api_key

    def generar_agente(self) -> dict:
        return {"proveedor": "Google Gemini", "modelo": self.model_name}

    def generar_contenido(self, prompt: str) -> str:
        return f"[Gemini - {self.model_name}] Respuesta generada para: '{prompt}'"


class LocalModelStrategy(IAStrategy):
    def __init__(self, model_path: str = "llama-3-8b-local"):
        self.model_path = model_path

    def generar_agente(self) -> dict:
        return {"proveedor": "Local LLM", "modelo": self.model_path}

    def generar_contenido(self, prompt: str) -> str:
        return f"[LocalModel - {self.model_path}] Respuesta generada offline para: '{prompt}'"


# ==============================================================================
# 3. MODELOS DE DOMINIO Y MAPEO SQLALCHEMY
# ==============================================================================
pregunta_tags = db.Table(
    "pregunta_tags",
    db.Column("pregunta_id", db.Integer, db.ForeignKey("pregunta.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Autor(db.Model):
    __tablename__ = "autor"

    id = db.Column(db.Integer, primary_key=True)
    tipo_autor = db.Column(db.String(50), nullable=False)

    preguntas = db.relationship("Pregunta", back_populates="autor", lazy=True)
    respuestas = db.relationship("Respuesta", back_populates="autor", lazy=True)

    __mapper_args__ = {
        "polymorphic_identity": "autor",
        "polymorphic_on": tipo_autor,
    }

    def generar_respuesta(self, pregunta, texto: str = None):
        raise NotImplementedError("Las subclases deben implementar generar_respuesta()")


class User(Autor):
    __tablename__ = "user"

    id = db.Column(db.Integer, db.ForeignKey("autor.id"), primary_key=True)
    correo_electronico = db.Column(db.String(120), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(256), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "user",
    }

    def __init__(self, correo_electronico: str, contrasena: str):
        self.correo_electronico = correo_electronico
        self.set_contrasena(contrasena)

    def set_contrasena(self, contrasena: str):
        self.contrasena_hash = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena: str) -> bool:
        return check_password_hash(self.contrasena_hash, contrasena)

    def es_admin(self) -> bool:
        return False

    def generar_pregunta(self, titulo: str, texto: str, categoria, tags: list):
        if not tags or len(tags) < 1:
            raise ValueError("Una pregunta debe tener al menos una etiqueta (Tag) [1..*].")
        return Pregunta(
            titulo=titulo,
            texto=texto,
            autor=self,
            categoria=categoria,
            tags=tags,
        )

    def generar_respuesta(self, pregunta, texto: str = None):
        if not texto:
            raise ValueError("El usuario debe proveer el texto de la respuesta.")
        return UserResponse(texto=texto, autor=self, pregunta=pregunta)

    def aceptar_respuesta(self, respuesta):
        if respuesta.pregunta.autor_id != self.id:
            raise PermissionError("Solo el autor de la pregunta puede aceptar una respuesta.")
        respuesta.aceptada = True

    def votar(self, respuesta, delta: int = 1):
        respuesta.puntuacion += delta
        respuesta.calcular_puntuacion()


class Usuario(User):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "usuario"}


class Admin(User):
    __tablename__ = "admin"
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "admin"}

    def es_admin(self) -> bool:
        return True

    def generar_tag(self, descripcion: str):
        return Tag(descripcion=descripcion)

    def generar_categoria(self, descripcion: str):
        return Categoria(descripcion=descripcion)


class AgenteIA(Autor):
    __tablename__ = "agente_ia"

    id = db.Column(db.Integer, db.ForeignKey("autor.id"), primary_key=True)
    nombre_estrategia = db.Column(db.String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "agente_ia",
    }

    def __init__(self, strategy: IAStrategy):
        self._strategy = strategy
        self.nombre_estrategia = strategy.__class__.__name__

    @property
    def strategy(self) -> IAStrategy:
        if not hasattr(self, "_strategy") or self._strategy is None:
            mapa = {
                "OpenAIStrategy": OpenAIStrategy,
                "GeminiStrategy": GeminiStrategy,
                "LocalModelStrategy": LocalModelStrategy,
            }
            self._strategy = mapa.get(self.nombre_estrategia, OpenAIStrategy)()
        return self._strategy

    @strategy.setter
    def strategy(self, nueva_estrategia: IAStrategy):
        self._strategy = nueva_estrategia
        self.nombre_estrategia = nueva_estrategia.__class__.__name__

    def generar_respuesta(self, pregunta, texto: str = None):
        prompt = f"{pregunta.titulo}: {pregunta.texto}"
        contenido_generado = self.strategy.generar_contenido(prompt)
        return AgenteIAResponse(texto=contenido_generado, autor=self, pregunta=pregunta)


class Categoria(db.Model):
    __tablename__ = "categoria"
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), unique=True, nullable=False)
    preguntas = db.relationship("Pregunta", back_populates="categoria", lazy=True)


class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(50), unique=True, nullable=False)


class Pregunta(db.Model):
    __tablename__ = "pregunta"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.Integer, default=lambda: int(datetime.utcnow().timestamp()), nullable=False)

    autor_id = db.Column(db.Integer, db.ForeignKey("autor.id"), nullable=False)
    autor = db.relationship("Autor", back_populates="preguntas")

    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    categoria = db.relationship("Categoria", back_populates="preguntas")

    tags = db.relationship("Tag", secondary=pregunta_tags, lazy="subquery")
    respuestas = db.relationship("Respuesta", back_populates="pregunta", lazy=True)


class Respuesta(db.Model):
    __tablename__ = "respuesta"
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    aceptada = db.Column(db.Boolean, default=False, nullable=False)
    puntuacion = db.Column(db.Integer, default=0, nullable=False)
    tipo_respuesta = db.Column(db.String(50), nullable=False)

    autor_id = db.Column(db.Integer, db.ForeignKey("autor.id"), nullable=False)
    autor = db.relationship("Autor", back_populates="respuestas")

    pregunta_id = db.Column(db.Integer, db.ForeignKey("pregunta.id"), nullable=False)
    pregunta = db.relationship("Pregunta", back_populates="respuestas")

    __mapper_args__ = {
        "polymorphic_identity": "respuesta",
        "polymorphic_on": tipo_respuesta,
    }

    def calcular_puntuacion(self) -> int:
        return self.puntuacion + (10 if self.aceptada else 0)


class UserResponse(Respuesta):
    __tablename__ = "user_response"
    id = db.Column(db.Integer, db.ForeignKey("respuesta.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "user_response"}


class AgenteIAResponse(Respuesta):
    __tablename__ = "agente_ia_response"
    id = db.Column(db.Integer, db.ForeignKey("respuesta.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "agente_ia_response"}


# ==============================================================================
# 4. PATRONES ABSTRACT FACTORY & FACTORY METHOD
# ==============================================================================
class FabricaAutor(ABC):
    @abstractmethod
    def crear_autor(self, **kwargs) -> Autor:
        pass


class FabricaUser(FabricaAutor):
    def crear_autor(self, correo_electronico: str, contrasena: str, es_admin: bool = False) -> Autor:
        if es_admin:
            return Admin(correo_electronico=correo_electronico, contrasena=contrasena)
        return Usuario(correo_electronico=correo_electronico, contrasena=contrasena)


class FabricaAgIA(FabricaAutor):
    ESTRATEGIAS_DISPONIBLES = {
        "openai": OpenAIStrategy,
        "gemini": GeminiStrategy,
        "local": LocalModelStrategy,
    }

    def crear_autor(self, proveedor: str = "openai", strategy: IAStrategy = None) -> AgenteIA:
        if strategy is not None:
            return AgenteIA(strategy=strategy)
        clase_estrategia = self.ESTRATEGIAS_DISPONIBLES.get(proveedor.lower())
        if not clase_estrategia:
            raise ValueError(f"Proveedor de IA no soportado: {proveedor}")
        return AgenteIA(strategy=clase_estrategia())


class RespuestaFactory:
    @staticmethod
    def crear_respuesta(autor: Autor, pregunta: Pregunta, texto: str = None) -> Respuesta:
        return autor.generar_respuesta(pregunta=pregunta, texto=texto)


# ==============================================================================
# 5. PLANTILLA HTML / CSS INTEGRADA
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Foro Q&A + Agentes IA (Patrones Strategy & Factory)</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-2: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text: #f8fafc;
            --muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body {
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }
        header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        header h1 { margin: 0; font-size: 1.25rem; color: #fff; }
        .badge {
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-admin { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
        .badge-user { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
        .badge-ia { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid #8b5cf6; }
        .badge-cat { background: #0284c7; color: #fff; }
        .badge-tag { background: var(--surface-2); color: var(--muted); }
        .badge-ok { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }

        .container {
            max-width: 1150px;
            margin: 1.5rem auto;
            padding: 0 1rem;
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 1.5rem;
        }
        @media (max-width: 850px) { .container { grid-template-columns: 1fr; } }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1.25rem;
        }
        .card h2, .card h3 { margin-top: 0; font-size: 1.05rem; color: #e2e8f0; }

        input, textarea, select {
            width: 100%;
            padding: 0.55rem 0.75rem;
            margin-top: 0.3rem;
            margin-bottom: 0.8rem;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: #0f172a;
            color: var(--text);
            font-size: 0.9rem;
        }
        label { font-size: 0.82rem; color: var(--muted); display: block; }

        button {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.55rem 0.95rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: 0.15s;
        }
        button:hover { background: var(--primary-hover); }
        button.btn-ia { background: var(--accent); }
        button.btn-ia:hover { background: #7c3aed; }
        button.btn-success { background: var(--success); }
        button.btn-danger { background: var(--danger); }
        button.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.78rem; }

        .flash {
            max-width: 1150px;
            margin: 1rem auto 0;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid var(--primary);
            color: #93c5fd;
        }
        .tag-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.4rem 0 0.9rem;
        }
        .tag-check {
            background: #0f172a;
            border: 1px solid var(--border);
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            cursor: pointer;
        }
        .tag-check input { width: auto; margin: 0; }

        .respuesta {
            background: #0f172a;
            border-left: 3px solid var(--primary);
            padding: 0.85rem 1rem;
            border-radius: 6px;
            margin-top: 0.75rem;
        }
        .respuesta.ia { border-left-color: var(--accent); }
        .respuesta.aceptada { border: 1px solid var(--success); border-left-width: 4px; }
        .resp-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: var(--muted);
            margin-bottom: 0.4rem;
            flex-wrap: wrap;
            gap: 0.4rem;
        }
        .inline-form { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
        .inline-form input, .inline-form select { margin: 0; }
    </style>
</head>
<body>

<header>
    <h1>Foro Q&amp;A &bull; Patrones Strategy &amp; Factory</h1>
    <div>
        {% if usuario_actual %}
            <span style="margin-right: 0.6rem; font-size: 0.9rem;">
                {{ usuario_actual.correo_electronico }}
                {% if usuario_actual.es_admin() %}
                    <span class="badge badge-admin">Admin</span>
                {% else %}
                    <span class="badge badge-user">Usuario</span>
                {% endif %}
            </span>
            <a href="{{ url_for('logout') }}"><button class="btn-danger btn-sm">Cerrar sesión</button></a>
        {% else %}
            <span style="color: var(--muted); font-size: 0.85rem;">No has iniciado sesión</span>
        {% endif %}
    </div>
</header>

{% with messages = get_flashed_messages() %}
  {% if messages %}
    {% for msg in messages %}
      <div class="flash">{{ msg }}</div>
    {% endfor %}
  {% endif %}
{% endwith %}

<div class="container">
    <!-- COLUMNA IZQUIERDA: ACCESO Y ADMIN -->
    <aside>
        {% if not usuario_actual %}
        <div class="card">
            <h2>Iniciar Sesión</h2>
            <form method="POST" action="{{ url_for('login') }}">
                <label>Correo electrónico</label>
                <input type="email" name="correo_electronico" placeholder="camila@unrc.edu.ar" required>
                <label>Contraseña</label>
                <input type="password" name="contrasena" placeholder="••••••" required>
                <button type="submit" style="width: 100%;">Ingresar</button>
            </form>
            <div style="margin-top: 0.8rem; font-size: 0.78rem; color: var(--muted);">
                <strong>Cuentas de prueba:</strong><br>
                &bull; Admin: <code>admin@foro.com</code> / <code>admin123</code><br>
                &bull; Usuario: <code>camila@unrc.edu.ar</code> / <code>pass123</code>
            </div>
        </div>

        <div class="card">
            <h2>Registrarse</h2>
            <form method="POST" action="{{ url_for('register') }}">
                <label>Correo electrónico</label>
                <input type="email" name="correo_electronico" required>
                <label>Contraseña</label>
                <input type="password" name="contrasena" required>
                <label class="tag-check" style="margin-bottom: 0.8rem;">
                    <input type="checkbox" name="es_admin" value="1"> Registrar como Administrador
                </label>
                <button type="submit" style="width: 100%; background: var(--surface-2);">Crear cuenta</button>
            </form>
        </div>
        {% else %}
            {% if usuario_actual.es_admin() %}
            <div class="card" style="border-color: var(--warning);">
                <h2>Panel Administrador</h2>
                <form method="POST" action="{{ url_for('crear_categoria') }}">
                    <label>Nueva Categoría (1 por pregunta)</label>
                    <input type="text" name="descripcion" placeholder="Ej: Bases de Datos" required>
                    <button type="submit" style="width: 100%; background: var(--warning); color: #000;">+ Agregar Categoría</button>
                </form>
                <hr style="border-color: var(--border); margin: 1rem 0;">
                <form method="POST" action="{{ url_for('crear_tag') }}">
                    <label>Nuevo Tag (1..* por pregunta)</label>
                    <input type="text" name="descripcion" placeholder="Ej: SQLAlchemy" required>
                    <button type="submit" style="width: 100%; background: var(--warning); color: #000;">+ Agregar Tag</button>
                </form>
            </div>
            {% endif %}

            <div class="card">
                <h2>Nueva Pregunta</h2>
                <form method="POST" action="{{ url_for('crear_pregunta') }}">
                    <label>Título</label>
                    <input type="text" name="titulo" placeholder="Escribe el título..." required>

                    <label>Detalle</label>
                    <textarea name="texto" rows="3" placeholder="Describe tu consulta..." required></textarea>

                    <label>Categoría (Obligatoria - 1)</label>
                    <select name="categoria_id" required>
                        {% for c in categorias %}
                            <option value="{{ c.id }}">{{ c.descripcion }}</option>
                        {% endfor %}
                    </select>

                    <label>Tags (Selecciona 1 o más)</label>
                    <div class="tag-grid">
                        {% for t in tags %}
                            <label class="tag-check">
                                <input type="checkbox" name="tag_ids" value="{{ t.id }}"> {{ t.descripcion }}
                            </label>
                        {% endfor %}
                    </div>

                    <button type="submit" style="width: 100%;">Publicar Pregunta</button>
                </form>
            </div>
        {% endif %}
    </aside>

    <!-- COLUMNA DERECHA: PREGUNTAS Y RESPUESTAS -->
    <main>
        {% for p in preguntas %}
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                <span class="badge badge-cat">{{ p.categoria.descripcion }}</span>
                <span style="font-size: 0.8rem; color: var(--muted);">
                    Publicado por: <strong>{{ p.autor.correo_electronico if p.autor.correo_electronico else 'AgenteIA' }}</strong>
                </span>
            </div>

            <h2 style="font-size: 1.2rem; margin: 0.5rem 0;">{{ p.titulo }}</h2>
            <p style="margin: 0.4rem 0 0.8rem; color: #cbd5e1;">{{ p.texto }}</p>

            <div style="margin-bottom: 1rem;">
                {% for t in p.tags %}
                    <span class="badge badge-tag">#{{ t.descripcion }}</span>
                {% endfor %}
            </div>

            <!-- GENERAR RESPUESTA CON AGENTE IA (STRATEGY + ABSTRACT FACTORY) -->
            <div style="background: rgba(139, 92, 246, 0.08); border: 1px dashed var(--accent); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;">
                <strong style="font-size: 0.82rem; color: #c4b5fd;">Solicitar respuesta a AgenteIA (Patrón Strategy):</strong>
                <form class="inline-form" method="POST" action="{{ url_for('responder_ia', pregunta_id=p.id) }}">
                    <select name="proveedor" style="max-width: 240px;">
                        <option value="openai">OpenAIStrategy (GPT-4o)</option>
                        <option value="gemini">GeminiStrategy (Gemini 2.5 Pro)</option>
                        <option value="local">LocalModelStrategy (Llama-3 Local)</option>
                    </select>
                    <button type="submit" class="btn-ia">Generar Respuesta IA</button>
                </form>
            </div>

            <!-- RESPUESTAS -->
            <h3 style="font-size: 0.92rem; color: var(--muted);">Respuestas ({{ p.respuestas|length }})</h3>
            {% for r in p.respuestas %}
                <div class="respuesta {{ 'ia' if r.tipo_respuesta == 'agente_ia_response' else '' }} {{ 'aceptada' if r.aceptada else '' }}">
                    <div class="resp-header">
                        <div>
                            {% if r.tipo_respuesta == 'agente_ia_response' %}
                                <span class="badge badge-ia">AgenteIA ({{ r.autor.nombre_estrategia }})</span>
                            {% else %}
                                <span class="badge badge-user">{{ r.autor.correo_electronico }}</span>
                            {% endif %}
                            {% if r.aceptada %}
                                <span class="badge badge-ok">&#10003; Aceptada (+10 pts)</span>
                            {% endif %}
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.4rem;">
                            <span>Puntaje: <strong>{{ r.calcular_puntuacion() }}</strong></span>
                            {% if usuario_actual %}
                                <form method="POST" action="{{ url_for('votar_respuesta', respuesta_id=r.id) }}" style="margin:0;">
                                    <button type="submit" class="btn-sm" style="background: var(--surface-2);">+1 Voto</button>
                                </form>
                                {% if usuario_actual.id == p.autor_id and not r.aceptada %}
                                    <form method="POST" action="{{ url_for('aceptar_respuesta', respuesta_id=r.id) }}" style="margin:0;">
                                        <button type="submit" class="btn-sm btn-success">Aceptar</button>
                                    </form>
                                {% endif %}
                            {% endif %}
                        </div>
                    </div>
                    <div>{{ r.texto }}</div>
                </div>
            {% endfor %}

            <!-- RESPONDER COMO USUARIO -->
            {% if usuario_actual %}
                <form class="inline-form" method="POST" action="{{ url_for('responder_usuario', pregunta_id=p.id) }}">
                    <input type="text" name="texto" placeholder="Escribe tu respuesta como {{ usuario_actual.correo_electronico }}..." required>
                    <button type="submit">Responder</button>
                </form>
            {% endif %}
        </div>
        {% endfor %}
    </main>
</div>

</body>
</html>
"""


# ==============================================================================
# 6. RUTAS DE LA APLICACIÓN WEB
# ==============================================================================
@app.route("/")
def index():
    user_id = session.get("user_id")
    usuario_actual = db.session.get(User, user_id) if user_id else None
    preguntas = Pregunta.query.order_by(Pregunta.id.desc()).all()
    categorias = Categoria.query.all()
    tags = Tag.query.all()

    return render_template_string(
        HTML_TEMPLATE,
        usuario_actual=usuario_actual,
        preguntas=preguntas,
        categorias=categorias,
        tags=tags,
    )


@app.route("/register", methods=["POST"])
def register():
    correo = request.form.get("correo_electronico")
    contrasena = request.form.get("contrasena")
    es_admin = bool(request.form.get("es_admin"))

    if User.query.filter_by(correo_electronico=correo).first():
        flash("Error: Ese correo electrónico ya está registrado.")
        return redirect(url_for("index"))

    nuevo_usuario = FabricaUser().crear_autor(
        correo_electronico=correo,
        contrasena=contrasena,
        es_admin=es_admin,
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    session["user_id"] = nuevo_usuario.id
    flash(f"Cuenta creada correctamente ({'Admin' if es_admin else 'Usuario'}).")
    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    correo = request.form.get("correo_electronico")
    contrasena = request.form.get("contrasena")

    usuario = User.query.filter_by(correo_electronico=correo).first()
    if not usuario or not usuario.verificar_contrasena(contrasena):
        flash("Credenciales inválidas. Verifica correo y contraseña.")
        return redirect(url_for("index"))

    session["user_id"] = usuario.id
    flash(f"Bienvenido/a {usuario.correo_electronico} (Rol: {'Admin' if usuario.es_admin() else 'Usuario'}).")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("index"))


@app.route("/admin/categorias", methods=["POST"])
def crear_categoria():
    usuario = db.session.get(User, session.get("user_id"))
    if not usuario or not usuario.es_admin():
        flash("Acceso denegado: solo administradores.")
        return redirect(url_for("index"))

    desc = request.form.get("descripcion", "").strip()
    if desc and not Categoria.query.filter_by(descripcion=desc).first():
        db.session.add(usuario.generar_categoria(desc))
        db.session.commit()
        flash(f"Categoría '{desc}' creada.")
    return redirect(url_for("index"))


@app.route("/admin/tags", methods=["POST"])
def crear_tag():
    usuario = db.session.get(User, session.get("user_id"))
    if not usuario or not usuario.es_admin():
        flash("Acceso denegado: solo administradores.")
        return redirect(url_for("index"))

    desc = request.form.get("descripcion", "").strip()
    if desc and not Tag.query.filter_by(descripcion=desc).first():
        db.session.add(usuario.generar_tag(desc))
        db.session.commit()
        flash(f"Tag '#{desc}' creado.")
    return redirect(url_for("index"))


@app.route("/preguntas", methods=["POST"])
def crear_pregunta():
    usuario = db.session.get(User, session.get("user_id"))
    if not usuario:
        flash("Debes iniciar sesión para publicar.")
        return redirect(url_for("index"))

    categoria = db.session.get(Categoria, request.form.get("categoria_id"))
    tag_ids = request.form.getlist("tag_ids")
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    if not categoria or len(tags) < 1:
        flash("Error: Una pregunta debe tener 1 categoría y al menos 1 tag.")
        return redirect(url_for("index"))

    pregunta = usuario.generar_pregunta(
        titulo=request.form.get("titulo"),
        texto=request.form.get("texto"),
        categoria=categoria,
        tags=tags,
    )
    db.session.add(pregunta)
    db.session.commit()
    flash("Pregunta publicada correctamente.")
    return redirect(url_for("index"))


@app.route("/preguntas/<int:pregunta_id>/responder", methods=["POST"])
def responder_usuario(pregunta_id):
    usuario = db.session.get(User, session.get("user_id"))
    pregunta = db.session.get(Pregunta, pregunta_id)
    if usuario and pregunta:
        texto = request.form.get("texto")
        resp = RespuestaFactory.crear_respuesta(autor=usuario, pregunta=pregunta, texto=texto)
        db.session.add(resp)
        db.session.commit()
        flash("Respuesta publicada.")
    return redirect(url_for("index"))


@app.route("/preguntas/<int:pregunta_id>/responder-ia", methods=["POST"])
def responder_ia(pregunta_id):
    pregunta = db.session.get(Pregunta, pregunta_id)
    if pregunta:
        proveedor = request.form.get("proveedor", "openai")
        agente = FabricaAgIA().crear_autor(proveedor=proveedor)
        db.session.add(agente)

        resp_ia = RespuestaFactory.crear_respuesta(autor=agente, pregunta=pregunta)
        db.session.add(resp_ia)
        db.session.commit()
        flash(f"AgenteIA respondió usando {agente.nombre_estrategia}.")
    return redirect(url_for("index"))


@app.route("/respuestas/<int:respuesta_id>/votar", methods=["POST"])
def votar_respuesta(respuesta_id):
    usuario = db.session.get(User, session.get("user_id"))
    resp = db.session.get(Respuesta, respuesta_id)
    if usuario and resp:
        usuario.votar(resp, delta=1)
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/respuestas/<int:respuesta_id>/aceptar", methods=["POST"])
def aceptar_respuesta(respuesta_id):
    usuario = db.session.get(User, session.get("user_id"))
    resp = db.session.get(Respuesta, respuesta_id)
    if usuario and resp:
        try:
            usuario.aceptar_respuesta(resp)
            db.session.commit()
            flash("Respuesta marcada como aceptada.")
        except PermissionError as e:
            flash(str(e))
    return redirect(url_for("index"))


# ==============================================================================
# 7. INICIALIZACIÓN DE BASE DE DATOS Y DATOS DE PRUEBA
# ==============================================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if not Autor.query.first():
            fabrica_user = FabricaUser()
            fabrica_ia = FabricaAgIA()

            admin = fabrica_user.crear_autor("admin@foro.com", "admin123", es_admin=True)
            alumno = fabrica_user.crear_autor("camila@unrc.edu.ar", "pass123", es_admin=False)
            agente = fabrica_ia.crear_autor(proveedor="openai")

            db.session.add_all([admin, alumno, agente])
            db.session.commit()

            cat = admin.generar_categoria("Ingeniería de Software")
            tag1 = admin.generar_tag("Patrones de Diseño")
            tag2 = admin.generar_tag("Python")
            db.session.add_all([cat, tag1, tag2])
            db.session.commit()

            preg = alumno.generar_pregunta(
                titulo="¿Cuándo usar Strategy vs Factory?",
                texto="Necesito desacoplar algoritmos y creación de objetos en Flask.",
                categoria=cat,
                tags=[tag1, tag2],
            )
            db.session.add(preg)
            db.session.commit()

            r1 = RespuestaFactory.crear_respuesta(agente, preg)
            agente.strategy = GeminiStrategy()
            r2 = RespuestaFactory.crear_respuesta(agente, preg)
            r3 = RespuestaFactory.crear_respuesta(alumno, preg, "¡Gracias por las respuestas!")

            db.session.add_all([r1, r2, r3])
            db.session.commit()

    app.run(debug=True)