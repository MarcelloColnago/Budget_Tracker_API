# 💰 Budget Tracker API

Uma API RESTful desenvolvida em **Python** e **FastAPI** para controle de finanças pessoais. O sistema permite o gerenciamento de categorias de gastos e o registro de despesas, contando com um sistema inteligente de alertas de teto de gastos.

## 🚀 O Problema que este projeto resolve
Muitas pessoas anotam o que gastam, mas só percebem que passaram do limite quando o dinheiro já acabou. Esta API resolve isso permitindo que o usuário defina um **teto mensal** para cada categoria. Sempre que uma nova despesa é registrada, o sistema calcula o total e emite alertas automáticos caso o usuário atinja 80% ou ultrapasse o limite estipulado.

## ✨ Funcionalidades (Regras de Negócio)
* **Gerenciamento de Categorias:** Criação de categorias com limites (tetos) de gastos personalizados.
* **Registro de Despesas:** Inclusão de gastos vinculados às categorias.
* **Validação Rigorosa:** Bloqueio de valores negativos, zerados ou categorias duplicadas (via Pydantic).
* **Alertas Inteligentes:** Retorno de avisos (`AVISO` ou `ALERTA_CRITICO`) no payload da resposta se o gasto ultrapassar as margens de segurança.
* **Persistência de Dados:** Banco de dados relacional integrado utilizando SQLite e SQLAlchemy.

## 🛠️ Tecnologias Utilizadas
* **Python 3+**
* **FastAPI:** Framework web moderno e rápido para construção de APIs.
* **Pydantic:** Validação e tipagem de dados.
* **SQLAlchemy:** ORM (Object-Relational Mapping) para comunicação com o banco de dados.
* **SQLite:** Banco de dados relacional leve e embutido.
* **Uvicorn:** Servidor ASGI para rodar a aplicação.

## 📂 Estrutura do Projeto
```text
PROJETO_WEB_PY/
├── app/
│   ├── __init__.py
│   ├── database.py      # Configuração do SQLite e SQLAlchemy
│   ├── main.py          # Rotas principais da API (Endpoints)
│   ├── models.py        # Modelos das tabelas do banco de dados
│   └── schemas.py       # Validações de entrada/saída com Pydantic
├── requirements.txt     # Dependências do projeto
└── budget.db            # Banco de dados gerado automaticamente