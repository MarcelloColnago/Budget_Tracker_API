from pydantic import BaseModel, Field

# Regras para criar uma nova Categoria de Gasto (Ex: Alimentação)
class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=50, description="Nome da categoria")
    teto_mensal: float = Field(..., gt=0, description="O limite máximo de gastos")

# Regras para registrar uma nova Despesa (Ex: Almoço)
class DespesaCreate(BaseModel):
    descricao: str = Field(..., min_length=3, description="O que você comprou")
    valor: float = Field(..., gt=0, description="Valor gasto")
    categoria_nome: str = Field(..., description="Nome da categoria deste gasto")