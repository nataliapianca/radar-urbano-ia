from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.classificacao import ClassificacaoIA


class Localizacao(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RelatoCriar(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    texto: str = Field(min_length=10, max_length=5000)
    localizacao: Localizacao


class StatusRelato(str, Enum):
    RECEBIDO = "Recebido"
    CLASSIFICADO = "Classificado"
    EM_ANDAMENTO = "Em andamento"
    RESOLVIDO = "Resolvido"


class RelatoResposta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    texto: str
    localizacao: Localizacao
    status: StatusRelato
    criado_em: datetime
    classificacao: ClassificacaoIA | None = None


class RelatosLista(BaseModel):
    relatos: list[RelatoResposta]
