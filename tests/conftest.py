"""Fixtures compartilhadas pelos testes do Radar Urbano IA.

Nenhum teste chama serviços externos: o Groq e o Geoapify são sempre
substituídos por dublês (fakes/monkeypatch). Por isso a suíte roda sem
internet e sem chaves de API.
"""
import os

# O UrbanIA lê USE_MOCK no momento do import e, fora do modo mock, cria o
# cliente OpenAI, que exige uma chave. Definimos o modo mock ANTES de qualquer
# import do módulo; o load_dotenv não sobrescreve variáveis já definidas, então
# um ia/.env local não interfere nos testes.
os.environ["USE_MOCK"] = "true"
os.environ.pop("GEOAPIFY_API_KEY", None)

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app


@pytest.fixture
def client():
    """Cliente HTTP com uma instância nova da API (repositório vazio)."""
    with TestClient(criar_app()) as cliente:
        yield cliente


@pytest.fixture
def relato_valido():
    return {
        "texto": "Há um poste apagado na Rua Sete de Setembro há três dias.",
        "localizacao": {"latitude": -20.3155, "longitude": -40.3128},
    }


@pytest.fixture
def classificacao_valida():
    return {
        "categoria": "Iluminação",
        "prioridade": "Média",
        "setor": "Iluminação Pública",
        "risco_associado": "Baixa visibilidade durante a noite.",
        "informacoes_relevantes": ["Poste apagado", "Problema há três dias"],
    }


@pytest.fixture
def criar_relato(client, relato_valido):
    """Cadastra um relato e devolve o JSON de resposta."""
    def _criar(**alteracoes):
        corpo = {**relato_valido, **alteracoes}
        resposta = client.post("/relatos", json=corpo)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()
    return _criar
