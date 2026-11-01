"""Testes unitários do módulo de IA (ia/UrbanIA.py).

O cliente do Groq é substituído por um dublê, então os testes verificam o
nosso código (prompt enviado, schema, validação e tratamento de erros) sem
gastar cota da API.
"""
import json
from types import SimpleNamespace

import httpx
import openai
import pytest

import UrbanIA


class ClienteFalso:
    """Imita client.chat.completions.create do SDK da OpenAI."""

    def __init__(self, conteudo=None, erro=None):
        self.conteudo, self.erro, self.chamadas = conteudo, erro, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        if self.erro:
            raise self.erro
        texto = self.conteudo if isinstance(self.conteudo, str) else json.dumps(self.conteudo)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=texto))])


@pytest.fixture
def ia_real(monkeypatch):
    """Desliga o mock e injeta o cliente falso no lugar do Groq."""
    def instalar(**kwargs):
        cliente = ClienteFalso(**kwargs)
        monkeypatch.setattr(UrbanIA, "USE_MOCK", False)
        monkeypatch.setattr(UrbanIA, "client", cliente)
        return cliente
    return instalar


RESPOSTA_OK = {
    "categoria": "Infraestrutura", "prioridade": "Alta", "setor": "Obras Viárias",
    "risco_associado": "Risco de acidente com veículos.",
    "informacoes_relevantes": ["Buraco de 90 cm", "Há 3 dias"],
}

_REQ = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


# --------------------------------------------------------------------------- #
# Modo mock
# --------------------------------------------------------------------------- #
def test_mock_devolve_classificacao_do_contrato(monkeypatch):
    monkeypatch.setattr(UrbanIA, "USE_MOCK", True)
    resultado = UrbanIA.classificar_relato("qualquer texto")
    assert resultado == UrbanIA.MOCK_CLASSIFICACAO
    UrbanIA.Classificacao(**resultado)  # respeita o próprio schema


def test_mock_devolve_copia(monkeypatch):
    monkeypatch.setattr(UrbanIA, "USE_MOCK", True)
    UrbanIA.classificar_relato("x")["categoria"] = "Trânsito"
    assert UrbanIA.MOCK_CLASSIFICACAO["categoria"] == "Iluminação"


def test_mock_verificacao(monkeypatch):
    monkeypatch.setattr(UrbanIA, "USE_MOCK", True)
    assert UrbanIA.verificar_relato("x") == {"suficiente": True, "pergunta": ""}


# --------------------------------------------------------------------------- #
# Chamada ao modelo
# --------------------------------------------------------------------------- #
def test_classificacao_valida_e_devolvida(ia_real):
    ia_real(conteudo=RESPOSTA_OK)
    assert UrbanIA.classificar_relato("Buraco de 90 cm na rua há 3 dias") == RESPOSTA_OK


def test_requisicao_usa_modelo_prompt_e_schema_estrito(ia_real):
    cliente = ia_real(conteudo=RESPOSTA_OK)
    UrbanIA.classificar_relato("Buraco na rua")
    chamada = cliente.chamadas[0]
    assert chamada["model"] == "openai/gpt-oss-120b"
    assert chamada["temperature"] == 0
    assert chamada["messages"][0] == {"role": "system", "content": UrbanIA.PROMPT_SISTEMA}
    assert chamada["messages"][1] == {"role": "user", "content": "Buraco na rua"}
    schema = chamada["response_format"]["json_schema"]
    assert schema["strict"] is True
    assert schema["schema"] == UrbanIA.SCHEMA_RESPOSTA


def test_enums_do_schema_iguais_aos_do_backend():
    """Se o backend mudar uma categoria/prioridade, a IA precisa acompanhar."""
    from app.schemas.classificacao import Categoria, Prioridade
    props = UrbanIA.SCHEMA_RESPOSTA["properties"]
    assert props["categoria"]["enum"] == [c.value for c in Categoria]
    assert props["prioridade"]["enum"] == [p.value for p in Prioridade]


def test_espacos_extras_sao_removidos(ia_real):
    ia_real(conteudo={**RESPOSTA_OK, "setor": "  Obras Viárias  "})
    assert UrbanIA.classificar_relato("x")["setor"] == "Obras Viárias"


@pytest.mark.parametrize("alteracao", [
    {"categoria": "Saneamento"},
    {"prioridade": "Urgente"},
    {"setor": ""},
    {"informacoes_relevantes": ["x"] * 21},
    {"campo_extra": "não previsto"},
])
def test_resposta_fora_do_contrato_vira_erro_ia(ia_real, alteracao):
    ia_real(conteudo={**RESPOSTA_OK, **alteracao})
    with pytest.raises(UrbanIA.ErroIA, match="fora do formato"):
        UrbanIA.classificar_relato("x")


def test_resposta_que_nao_e_json_vira_erro_ia(ia_real):
    ia_real(conteudo="Desculpe, não consigo classificar.")
    with pytest.raises(UrbanIA.ErroIA, match="JSON"):
        UrbanIA.classificar_relato("x")


@pytest.mark.parametrize("erro,trecho", [
    (openai.AuthenticationError("401", response=httpx.Response(401, request=_REQ), body=None), "Chave"),
    (openai.RateLimitError("429", response=httpx.Response(429, request=_REQ), body=None), "Limite"),
    (openai.APITimeoutError(request=_REQ), "demorou"),
    (openai.APIConnectionError(request=_REQ), "conectar"),
    (openai.InternalServerError("500", response=httpx.Response(500, request=_REQ), body=None), "erro"),
])
def test_erros_do_groq_viram_mensagens_em_portugues(ia_real, erro, trecho):
    ia_real(erro=erro)
    with pytest.raises(UrbanIA.ErroIA, match=trecho):
        UrbanIA.classificar_relato("x")


def test_verificacao_com_pergunta(ia_real):
    ia_real(conteudo={"suficiente": False, "pergunta": "Em qual rua fica o problema?"})
    assert UrbanIA.verificar_relato("Tem um buraco") == {
        "suficiente": False, "pergunta": "Em qual rua fica o problema?"}


def test_verificacao_fora_do_formato(ia_real):
    ia_real(conteudo={"suficiente": "talvez"})
    with pytest.raises(UrbanIA.ErroIA):
        UrbanIA.verificar_relato("x")
