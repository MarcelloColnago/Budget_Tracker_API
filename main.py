from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas import CategoriaCreate, DespesaCreate
from app.database import SessionLocal, engine, Base
from app.models import CategoriaModel, DespesaModel

# Cria tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budget Tracker API", version="0.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HOME
@app.get("/")
def home():
    return FileResponse("index.html")


# -----------------------------
# CATEGORIAS
# -----------------------------

@app.post("/categorias/")
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nome_limpo = categoria.nome.lower().strip()

    db_categoria = db.query(CategoriaModel).filter(
        CategoriaModel.nome == nome_limpo
    ).first()

    if db_categoria:
        raise HTTPException(status_code=400, detail="Essa categoria já existe!")

    nova_categoria = CategoriaModel(
        nome=nome_limpo,
        teto_mensal=categoria.teto_mensal
    )

    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)

    return {"mensagem": f"Categoria '{categoria.nome}' salva no banco de dados!"}


@app.get("/categorias/")
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(CategoriaModel).all()


# -----------------------------
# DESPESAS
# -----------------------------

@app.get("/despesas/")
def listar_todas_despesas(db: Session = Depends(get_db)):
    return db.query(DespesaModel).all()


@app.post("/despesas/")
def registrar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)):
    cat_nome = despesa.categoria_nome.lower().strip()

    categoria = db.query(CategoriaModel).filter(
        CategoriaModel.nome == cat_nome
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada no banco!")

    categoria.total_gasto += despesa.valor

    nova_despesa = DespesaModel(
        descricao=despesa.descricao,
        valor=despesa.valor,
        categoria_nome=cat_nome
    )

    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)

    resposta = {
        "mensagem": "Despesa persistida com sucesso!",
        "dados": {
            "id": nova_despesa.id,
            "descricao": nova_despesa.descricao,
            "valor": nova_despesa.valor,
            "categoria": categoria.nome
        }
    }

    if categoria.total_gasto >= categoria.teto_mensal:
        resposta["ALERTA_CRITICO"] = "⚠️ Teto ESTOURADO!"
    elif categoria.total_gasto >= (categoria.teto_mensal * 0.8):
        resposta["AVISO"] = "🔔 Mais de 80% do teto atingido!"

    return resposta

# -----------------------------
# DELETAR DESPESAS 
# -----------------------------

@app.delete("/despesas/{despesa_id}")
def excluir_despesa(despesa_id: int, db: Session = Depends(get_db)):
    # 1. Busca a despesa
    despesa = db.query(DespesaModel).filter(DespesaModel.id == despesa_id).first()
    
    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada!")

    # 2. Busca a categoria para atualizar o total_gasto
    categoria = db.query(CategoriaModel).filter(CategoriaModel.nome == despesa.categoria_nome).first()
    
    if categoria:
        categoria.total_gasto -= despesa.valor
    
    # 3. Remove a despesa
    db.delete(despesa)
    db.commit()
    
    return {"mensagem": f"Despesa '{despesa.descricao}' (id: {despesa_id}) excluída com sucesso!"}


# -----------------------------
# LISTAR DESPESAS 
# -----------------------------

@app.get("/despesas/{categoria_nome}")
def listar_despesas_por_categoria(categoria_nome: str, db: Session = Depends(get_db)):
    # Busca todas as despesas daquela categoria
    despesas = db.query(DespesaModel).filter(DespesaModel.categoria_nome == categoria_nome.lower()).all()
    
    if not despesas:
        raise HTTPException(status_code=404, detail="Nenhuma despesa encontrada para esta categoria.")
    
    return despesas

@app.delete("/categorias/{nome}")
def excluir_categoria(nome: str, db: Session = Depends(get_db)):
    # 1. Busca a categoria
    categoria = db.query(CategoriaModel).filter(CategoriaModel.nome == nome).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada!")
    
    # 2. Apaga todas as despesas desta categoria primeiro
    db.query(DespesaModel).filter(DespesaModel.categoria_nome == nome).delete()
    
    # 3. Apaga a categoria
    db.delete(categoria)
    db.commit()
    return {"mensagem": "Categoria e despesas excluídas!"}