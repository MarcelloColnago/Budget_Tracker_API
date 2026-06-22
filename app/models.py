from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base
from datetime import date

class CategoriaModel(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    teto_mensal = Column(Float)
    total_gasto = Column(Float, default=0.0)

class DespesaModel(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    valor = Column(Float)
    categoria_nome = Column(String)
    data = Column(Date, default=date.today)