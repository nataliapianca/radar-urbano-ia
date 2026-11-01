import os
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.classificacao import ClassificacaoIA
from app.geocodificacao import GeocodificacaoIndisponivel, buscar_endereco
from app.repositorio import RepositorioRelatos
from app.schemas.relatos import (
    EnderecoBusca,
    OpcoesLocalizacao,
    RelatoCriar,
    RelatoResposta,
    RelatosLista,
)


def criar_app() -> FastAPI:
    app = FastAPI(title="Radar Urbano IA", version="0.2.0",
                  description="API para registro e classificação de problemas urbanos")
    app.state.repositorio = RepositorioRelatos()
    origens = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origens.split(",") if o.strip()],
        allow_methods=["GET", "POST", "PUT"], allow_headers=["Content-Type"],
    )

    @app.get("/")
    def read_root():
        return {"status": "online", "mensagem": "API do Radar Urbano IA rodando"}

    @app.post("/relatos", response_model=RelatoResposta, status_code=201)
    def criar_relato(dados: RelatoCriar, request: Request):
        return request.app.state.repositorio.criar(dados)

    @app.post("/localizacoes/buscar", response_model=OpcoesLocalizacao)
    def buscar_localizacao(dados: EnderecoBusca):
        try:
            return OpcoesLocalizacao(resultados=buscar_endereco(dados.endereco))
        except GeocodificacaoIndisponivel as erro:
            raise HTTPException(status_code=503, detail=str(erro)) from erro

    @app.get("/relatos", response_model=RelatosLista)
    def listar_relatos(request: Request):
        return RelatosLista(relatos=request.app.state.repositorio.listar())

    @app.get("/relatos/{relato_id}", response_model=RelatoResposta)
    def buscar_relato(relato_id: UUID, request: Request):
        relato = request.app.state.repositorio.buscar(relato_id)
        if relato is None:
            raise HTTPException(status_code=404, detail="Relato não encontrado")
        return relato

    @app.put("/relatos/{relato_id}/classificacao", response_model=RelatoResposta)
    def classificar_relato(relato_id: UUID, dados: ClassificacaoIA, request: Request):
        relato = request.app.state.repositorio.classificar(relato_id, dados)
        if relato is None:
            raise HTTPException(status_code=404, detail="Relato não encontrado")
        return relato

    return app


app = criar_app()
