from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas import CategoriaCreate, DespesaCreate
from app.database import SessionLocal, engine, Base
from app.models import CategoriaModel, DespesaModel

# Comando mágico: Varre o 'models.py' e cria o arquivo 'budget.db' com as tabelas se ele não existir
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budget Tracker API", version="0.2.0")

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware  # 1. IMPORTE ISSO
from sqlalchemy.orm import Session
# ... seus outros imports permanecem iguais ...

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budget Tracker API", version="0.2.0")

# 2. ADICIONE ESSE BLOCO LOGO AQUI:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que a sua página HTML acesse a API
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os comandos (POST, GET, etc.)
    allow_headers=["*"],
)
# Função de ajuda (Dependency) para abrir e fechar a conexão com o banco em cada clique
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return FileResponse("index.html")

# ----------------------------------------------------
# ROTAS DE CATEGORIAS (Agora no Banco de Dados)
# ----------------------------------------------------

@app.post("/categorias/")
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nome_limpo = categoria.nome.lower().strip()
    
    # Busca no banco se já existe uma categoria com esse nome
    db_categoria = db.query(CategoriaModel).filter(CategoriaModel.nome == nome_limpo).first()
    if db_categoria:
        raise HTTPException(status_code=400, detail="Essa categoria já existe!")
    
    # Cria o objeto da tabela
    nova_categoria = CategoriaModel(nome=nome_limpo, teto_mensal=categoria.teto_mensal)
    
    db.add(nova_categoria) # Prepara para salvar
    db.commit()            # Salva de verdade no arquivo
    db.refresh(nova_categoria)
    
    return {"mensagem": f"Categoria '{categoria.nome}' salva no banco de dados!"}

@app.get("/categorias/")
def listar_categorias(db: Session = Depends(get_db)):
    # Busca todas as categorias salvas no banco
    categorias = db.query(CategoriaModel).all()
    return categorias

# ----------------------------------------------------
# ROTAS DE DESPESAS (Agora no Banco de Dados)
# ----------------------------------------------------

@app.post("/despesas/")
def registrar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)):
    cat_nome = despesa.categoria_nome.lower().strip()
    
    # 1. Busca a categoria no banco de dados
    categoria = db.query(CategoriaModel).filter(CategoriaModel.nome == cat_nome).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada no banco!")
    
    # 2. Atualiza o valor do total gasto direto na tabela do banco
    categoria.total_gasto += despesa.valor
    
    # 3. Cria o registro da nova despesa
    nova_despesa = DespesaModel(
        descricao=despesa.descricao,
        valor=despesa.valor,
        categoria_nome=cat_nome
    )
    
    db.add(nova_despesa)
    db.commit() # Salva as alterações da categoria e a nova despesa de uma vez só!
    db.refresh(nova_despesa)
    
    # 4. LÓGICA DE ALERTA
    teto = categoria.teto_mensal
    gasto_atual = categoria.total_gasto
    
    resposta = {
        "mensagem": "Despesa persistida com sucesso!",
        "dados": {
            "id": nova_despesa.id,
            "descricao": nova_despesa.descricao,
            "valor": nova_despesa.valor,
            "categoria": categoria.nome
        }
    }
    
    if gasto_atual >= teto:
        resposta["ALERTA_CRITICO"] = f"⚠️ Teto ESTOURADO! (Gasto: R${gasto_atual:.2f} / Teto: R${teto:.2f})"
    elif gasto_atual >= (teto * 0.8):
        resposta["AVISO"] = f"🔔 Mais de 80% do teto atingido!"
        
    return resposta
