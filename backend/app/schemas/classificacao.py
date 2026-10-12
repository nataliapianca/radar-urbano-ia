from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Categoria(str, Enum):
    INFRAESTRUTURA = "Infraestrutura"
    ILUMINACAO = "Iluminação"
    LIMPEZA_URBANA = "Limpeza Urbana"
    TRANSITO = "Trânsito"
    SEGURANCA = "Segurança"
    MEIO_AMBIENTE = "Meio Ambiente"


class Prioridade(str, Enum):
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"


class ClassificacaoIA(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    categoria: Categoria
    prioridade: Prioridade
    setor: str = Field(min_length=1, max_length=150)
    risco_associado: str = Field(min_length=1, max_length=1000)
    informacoes_relevantes: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
