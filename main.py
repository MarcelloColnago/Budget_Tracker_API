from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date

from app.schemas import CategoriaCreate, DespesaCreate
from app.database import SessionLocal, engine, Base
from app.models import CategoriaModel, DespesaModel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budget Tracker API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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


@app.delete("/categorias/{nome}")
def excluir_categoria(nome: str, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaModel).filter(CategoriaModel.nome == nome).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada!")

    db.query(DespesaModel).filter(DespesaModel.categoria_nome == nome).delete()
    db.delete(categoria)
    db.commit()
    return {"mensagem": "Categoria e despesas excluídas!"}


# -----------------------------
# DESPESAS
# CORRIGIDO: rotas estáticas ANTES das dinâmicas
# /despesas/filtro estava sendo capturado por /despesas/{categoria_nome}
# -----------------------------

@app.get("/despesas/")
def listar_todas_despesas(db: Session = Depends(get_db)):
    return db.query(DespesaModel).all()


# CORRIGIDO: rota estática definida antes de /{categoria_nome}
@app.get("/despesas/filtro")
def filtrar_despesas(
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    despesas = db.query(DespesaModel).filter(
        DespesaModel.data >= inicio,
        DespesaModel.data <= fim
    ).all()

    return despesas


# Rota dinâmica DEPOIS das estáticas
@app.get("/despesas/{categoria_nome}")
def listar_despesas_por_categoria(categoria_nome: str, db: Session = Depends(get_db)):
    despesas = db.query(DespesaModel).filter(
        DespesaModel.categoria_nome == categoria_nome.lower()
    ).all()

    if not despesas:
        raise HTTPException(status_code=404, detail="Nenhuma despesa encontrada para esta categoria.")

    return despesas


@app.post("/despesas/")
def registrar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)):
    cat_nome = despesa.categoria_nome.lower().strip()

    categoria = db.query(CategoriaModel).filter(
        CategoriaModel.nome == cat_nome
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada no banco!")

    # CORRIGIDO: total recalculado do banco para evitar inconsistência ao reiniciar
    total_atual = sum(
        d.valor for d in db.query(DespesaModel).filter(
            DespesaModel.categoria_nome == cat_nome
        ).all()
    )
    categoria.total_gasto = total_atual + despesa.valor

    nova_despesa = DespesaModel(
        descricao=despesa.descricao,
        valor=despesa.valor,
        categoria_nome=cat_nome,
        data=despesa.data
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
            "categoria": categoria.nome,
            "data": nova_despesa.data.isoformat()
        }
    }

    if categoria.total_gasto >= categoria.teto_mensal:
        resposta["ALERTA_CRITICO"] = "⚠️ Teto ESTOURADO!"
    elif categoria.total_gasto >= (categoria.teto_mensal * 0.8):
        resposta["AVISO"] = "🔔 Mais de 80% do teto atingido!"

    return resposta


@app.delete("/despesas/{despesa_id}")
def excluir_despesa(despesa_id: int, db: Session = Depends(get_db)):
    despesa = db.query(DespesaModel).filter(DespesaModel.id == despesa_id).first()

    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada!")

    categoria = db.query(CategoriaModel).filter(
        CategoriaModel.nome == despesa.categoria_nome
    ).first()

    if categoria:
        # CORRIGIDO: max(0.0) evita total_gasto negativo
        categoria.total_gasto = max(0.0, categoria.total_gasto - despesa.valor)

    db.delete(despesa)
    db.commit()

    return {"mensagem": f"Despesa '{despesa.descricao}' (id: {despesa_id}) excluída com sucesso!"}


# CORRIGIDO: agora atualiza o total_gasto da categoria ao editar o valor
@app.put("/despesas/{id}")
def editar_despesa(id: int, dados: DespesaCreate, db: Session = Depends(get_db)):
    despesa = db.query(DespesaModel).filter(DespesaModel.id == id).first()

    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    categoria = db.query(CategoriaModel).filter(
        CategoriaModel.nome == despesa.categoria_nome
    ).first()

    if categoria:
        categoria.total_gasto = max(0.0, categoria.total_gasto - despesa.valor + dados.valor)

    despesa.descricao = dados.descricao
    despesa.valor = dados.valor
    despesa.data = dados.data

    db.commit()

    return {"mensagem": "Despesa atualizada"}


# -----------------------------
# DASHBOARD
# -----------------------------

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    categorias = db.query(CategoriaModel).all()
    despesas = db.query(DespesaModel).all()

    total_gasto = sum(d.valor for d in despesas)
    total_categorias = len(categorias)

    maior_categoria = None
    maior_gasto = 0

    for categoria in categorias:
        if categoria.total_gasto > maior_gasto:
            maior_gasto = categoria.total_gasto
            maior_categoria = categoria.nome

    return {
        "total_gasto": total_gasto,
        "total_categorias": total_categorias,
        "maior_categoria": maior_categoria,
        "maior_gasto": maior_gasto
    }