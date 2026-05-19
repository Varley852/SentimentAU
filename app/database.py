"""
SentimentAU - database.py
Configuração do banco de dados SQLite com SQLAlchemy.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

# ─────────────────────────────────────────────
# Configuração do engine e sessão
# ─────────────────────────────────────────────

DATABASE_URL = "sqlite:///./sentimentau.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necessário para SQLite com FastAPI
    echo=False,  # mude para True para ver os SQLs no terminal (útil ao debugar)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class NivelIntensidade(str, enum.Enum):
    """Escala visual de intensidade emocional (1 a 5).
    Simples e clara para usuários autistas.
    """
    MUITO_BAIXO = "1"
    BAIXO       = "2"
    MODERADO    = "3"
    ALTO        = "4"
    MUITO_ALTO  = "5"


class CategoriaEmocao(str, enum.Enum):
    """Categorias emocionais básicas reconhecidas pelo motor NLP."""
    ALEGRIA    = "alegria"
    TRISTEZA   = "tristeza"
    RAIVA      = "raiva"
    MEDO       = "medo"
    SURPRESA   = "surpresa"
    NOJO       = "nojo"
    ANSIEDADE  = "ansiedade"
    CALMA      = "calma"
    NEUTRO     = "neutro"


# ─────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────

class Usuario(Base):
    """Representa um usuário do diário emocional."""

    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, index=True)
    nome       = Column(String(100), nullable=False)
    criado_em  = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    entradas = relationship("EntradaDiario", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario id={self.id} nome='{self.nome}'>"


class EntradaDiario(Base):
    """Uma entrada do diário — texto livre escrito pelo usuário."""

    __tablename__ = "entradas_diario"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    texto      = Column(Text, nullable=False)
    criado_em  = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Intensidade escolhida manualmente pelo usuário (escala visual 1–5)
    intensidade_manual = Column(
        Enum(NivelIntensidade),
        nullable=True,
        comment="Intensidade informada pelo próprio usuário (1 a 5)",
    )

    # Relacionamentos
    usuario  = relationship("Usuario", back_populates="entradas")
    analises = relationship("AnaliseEmocional", back_populates="entrada", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EntradaDiario id={self.id} usuario_id={self.usuario_id}>"


class AnaliseEmocional(Base):
    """Resultado da análise NLP de uma entrada do diário.

    Gerada automaticamente pelo nlp_engine.py após cada entrada.
    Uma entrada pode gerar mais de uma emoção detectada.
    """

    __tablename__ = "analises_emocionais"

    id         = Column(Integer, primary_key=True, index=True)
    entrada_id = Column(Integer, ForeignKey("entradas_diario.id"), nullable=False)

    # Emoção principal detectada pelo NLP
    emocao     = Column(Enum(CategoriaEmocao), nullable=False)

    # Pontuação de sentimento: -1.0 (muito negativo) a +1.0 (muito positivo)
    polaridade = Column(Float, nullable=False, default=0.0)

    # Subjetividade: 0.0 (objetivo) a 1.0 (muito subjetivo)
    subjetividade = Column(Float, nullable=False, default=0.0)

    # Intensidade calculada pelo NLP (complementa a manual do usuário)
    intensidade_nlp = Column(
        Enum(NivelIntensidade),
        nullable=True,
        comment="Intensidade calculada automaticamente pelo NLP",
    )

    analisado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    entrada = relationship("EntradaDiario", back_populates="analises")

    def __repr__(self):
        return (
            f"<AnaliseEmocional id={self.id} emocao='{self.emocao}' "
            f"polaridade={self.polaridade:.2f}>"
        )


# ─────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────

def criar_tabelas():
    """Cria todas as tabelas no banco de dados (se não existirem)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Gerador de sessão para injeção de dependência no FastAPI.

    Uso nos endpoints:
        from database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @app.get("/exemplo")
        def rota(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
# Inicialização direta (teste rápido)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Criando tabelas do SentimentAU...")
    criar_tabelas()
    print("Tabelas criadas com sucesso!")
    print("Arquivo gerado: sentimentau.db")