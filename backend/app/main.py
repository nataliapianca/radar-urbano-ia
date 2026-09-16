from fastapi import FastAPI

#instancia da api, que vai receber requisições 
app = FastAPI(
    title="Radar Urbano IA",
    description="API da plataforma de registro e priorização de problemas urbanos",
    version="0.1.0"
)


#rota teste ora saber se servidor ta ativo
@app.get("/")
def read_root():
    return {"status": "online", "mensagem": "API do Radar Urbano IA rodando"}


#rota de exemplo atualemtne e so um placeholder
@app.get("/relatos")
def listar_relatos():
    return {"relatos": []}