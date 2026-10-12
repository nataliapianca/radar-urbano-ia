"""Dados temporários, mantidos apenas durante a execução do processo."""
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.classificacao import ClassificacaoIA
from app.schemas.relatos import RelatoCriar, RelatoResposta, StatusRelato


class RepositorioRelatos:
    def __init__(self):
        self._relatos: dict[UUID, RelatoResposta] = {}
        self._lock = Lock()

    def criar(self, dados: RelatoCriar) -> RelatoResposta:
        relato = RelatoResposta(
            id=uuid4(), texto=dados.texto,
            localizacao=dados.localizacao.model_copy(deep=True),
            status=StatusRelato.RECEBIDO, criado_em=datetime.now(timezone.utc),
        )
        with self._lock:
            self._relatos[relato.id] = relato
            return relato.model_copy(deep=True)

    def listar(self) -> list[RelatoResposta]:
        with self._lock:
            return [r.model_copy(deep=True) for r in self._relatos.values()]

    def buscar(self, relato_id: UUID) -> RelatoResposta | None:
        with self._lock:
            relato = self._relatos.get(relato_id)
            return relato.model_copy(deep=True) if relato else None

    def classificar(self, relato_id: UUID, dados: ClassificacaoIA) -> RelatoResposta | None:
        with self._lock:
            relato = self._relatos.get(relato_id)
            if relato is None:
                return None
            relato.classificacao = dados.model_copy(deep=True)
            if relato.status == StatusRelato.RECEBIDO:
                relato.status = StatusRelato.CLASSIFICADO
            return relato.model_copy(deep=True)
