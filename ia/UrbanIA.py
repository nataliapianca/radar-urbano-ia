import os
import json
from typing import Literal

import openai
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError

load_dotenv()

MODELO = "openai/gpt-oss-120b"

# Quando USE_MOCK=true no .env, as funções devolvem respostas fixas e não chamam o Groq
#implementar metodo para identificar se existe conexao com a internet a transforma em false para usar modelo pronto 
USE_MOCK = os.getenv("USE_MOCK", "false").strip().lower() == "true"

client = None
if not USE_MOCK:
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        timeout=30,       # desiste da chamada depois de 30 segundos
        max_retries=2,    # tenta de novo até 2 vezes em falhas temporárias
    )


class ErroIA(Exception):
    """Erro da IA com mensagem em português, pronta para mostrar ao usuário."""


# Validação do nosso lado: garante que a resposta respeita o contrato com o Backend
class Classificacao(BaseModel):
    # Mesmas regras do Backend: tira espaços das pontas e recusa campos a mais
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    categoria: Literal["Infraestrutura", "Iluminação", "Limpeza Urbana",
                       "Trânsito", "Segurança", "Meio Ambiente"]
    prioridade: Literal["Alta", "Média", "Baixa"]
    setor: str = Field(min_length=1, max_length=150)
    risco_associado: str = Field(min_length=1, max_length=1000)
    informacoes_relevantes: list[str] = Field(default_factory=list, max_length=20)


class Verificacao(BaseModel):
    suficiente: bool
    pergunta: str


def _chamar_groq(prompt_sistema, relato, nome_schema, schema):
    """Faz a chamada ao Groq e devolve o JSON da resposta como dicionário."""
    try:
        resposta = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": relato}
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": nome_schema,
                    "strict": True,
                    "schema": schema
                }
            }
        )
        return json.loads(resposta.choices[0].message.content)
    # A ordem importa: as exceções mais específicas vêm antes das mais gerais
    except openai.AuthenticationError as e:
        raise ErroIA("Chave da API do Groq inválida ou ausente. Verifique o GROQ_API_KEY no .env.") from e
    except openai.RateLimitError as e:
        raise ErroIA("Limite de uso do Groq atingido. Aguarde um pouco e tente novamente.") from e
    except openai.APITimeoutError as e:
        raise ErroIA("O Groq demorou demais para responder. Tente novamente.") from e
    except openai.APIConnectionError as e:
        raise ErroIA("Não foi possível conectar ao Groq. Verifique sua internet.") from e
    except openai.APIError as e:
        raise ErroIA(f"O Groq retornou um erro: {e}") from e
    except json.JSONDecodeError as e:
        raise ErroIA("A IA devolveu uma resposta que não é um JSON válido.") from e


PROMPT_SISTEMA = """
Você é um classificador de relatos urbanos.
Você NÃO conversa e NÃO dá conselhos. Apenas classifica.

Regras de prioridade:
- Alta: risco imediato à vida ou à integridade física (ex.: fio caído, buraco grande em via movimentada, vazamento perigoso).
- Média: problema que atrapalha ou pode causar dano se não for resolvido logo (ex.: poste apagado, semáforo com defeito).
- Baixa: incômodo sem risco imediato (ex.: mato alto, pichação, lixo pontual).

Setor: nome do setor responsável (ex.: "Iluminação Pública", "Obras Viárias").
Risco associado: uma frase curta explicando o risco do problema.
Informações relevantes: lista curta de detalhes importantes citados no relato (pode ser vazia).
"""

SCHEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "categoria": {
            "type": "string",
            "enum": ["Infraestrutura", "Iluminação", "Limpeza Urbana",
                     "Trânsito", "Segurança", "Meio Ambiente"]
        },
        "prioridade": {
            "type": "string",
            "enum": ["Alta", "Média", "Baixa"]
        },
        "setor": {"type": "string"},
        "risco_associado": {"type": "string"},
        "informacoes_relevantes": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["categoria", "prioridade", "setor",
                 "risco_associado", "informacoes_relevantes"],
    "additionalProperties": False
}

MOCK_CLASSIFICACAO = {
    "categoria": "Iluminação",
    "prioridade": "Média",
    "setor": "Iluminação Pública",
    "risco_associado": "Baixa visibilidade durante a noite.",
    "informacoes_relevantes": ["Poste apagado", "Problema há três dias"]
}


def classificar_relato(relato):
    if USE_MOCK:
        return dict(MOCK_CLASSIFICACAO)

    dados = _chamar_groq(PROMPT_SISTEMA, relato, "classificacao_relato", SCHEMA_RESPOSTA)
    try:
        return Classificacao(**dados).model_dump()
    except ValidationError as e:
        raise ErroIA("A IA devolveu uma classificação fora do formato combinado com o Backend.") from e


PROMPT_VERIFICACAO = """
Você é um assistente que verifica se um relato urbano tem informações suficientes para ser classificado.

Um relato completo precisa ter:
- Localização (rua, bairro ou ponto de referência)
- Tamanho ou gravidade do problema
- Há quanto tempo o problema existe

Se faltar alguma informação, faça UMA pergunta curta e educada pedindo o que falta.
Se o relato já tiver tudo, marque como suficiente e deixe a pergunta vazia.
"""

SCHEMA_VERIFICACAO = {
    "type": "object",
    "properties": {
        "suficiente": {"type": "boolean"},
        "pergunta": {"type": "string"}
    },
    "required": ["suficiente", "pergunta"],
    "additionalProperties": False
}

MOCK_VERIFICACAO = {"suficiente": True, "pergunta": ""}


def verificar_relato(relato):
    if USE_MOCK:
        return dict(MOCK_VERIFICACAO)

    dados = _chamar_groq(PROMPT_VERIFICACAO, relato, "verificacao_relato", SCHEMA_VERIFICACAO)
    try:
        return Verificacao(**dados).model_dump()
    except ValidationError as e:
        raise ErroIA("A IA devolveu uma verificação fora do formato esperado.") from e
