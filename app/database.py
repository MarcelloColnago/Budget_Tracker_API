from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Dizemos onde o arquivo do banco de dados vai ser criado (.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./budget.db"

# O engine é o motor que vai gerenciar a conexão com o arquivo
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cada requisição que chegar na API abrirá uma "SessionLocal" para conversar com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Essa classe Base será herdada por todos os nossos modelos de tabelas
Base = declarative_base()