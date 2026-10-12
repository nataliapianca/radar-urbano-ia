from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app.main import criar_app


@pytest.fixture
def client():
    with TestClient(criar_app()) as client:
        yield client


@pytest.fixture
def dados():
    return {"texto": "  Há um poste apagado na minha rua.  ",
            "localizacao": {"latitude": -20.3155, "longitude": -40.3128}}


def test_cadastro_e_consulta(client, dados):
    assert client.get("/relatos").json() == {"relatos": []}
    resposta = client.post("/relatos", json=dados)
    assert resposta.status_code == 201
    relato = resposta.json()
    assert relato["texto"] == dados["texto"].strip()
    assert relato["status"] == "Recebido"
    assert relato["classificacao"] is None
    assert relato["criado_em"]
    assert client.get(f"/relatos/{relato['id']}").json() == relato
    assert client.get("/relatos").json() == {"relatos": [relato]}


@pytest.mark.parametrize("texto", ["Oi", " " * 20, "a" * 5001])
def test_texto_invalido(client, dados, texto):
    dados["texto"] = texto
    assert client.post("/relatos", json=dados).status_code == 422
    assert client.get("/relatos").json() == {"relatos": []}


@pytest.mark.parametrize("campo,valor", [("latitude", 91), ("latitude", -91),
                                        ("longitude", 181), ("longitude", -181)])
def test_coordenadas_invalidas(client, dados, campo, valor):
    dados["localizacao"][campo] = valor
    assert client.post("/relatos", json=dados).status_code == 422


def test_campos_obrigatorios_e_extras(client, dados):
    assert client.post("/relatos", json={"texto": dados["texto"]}).status_code == 422
    dados["campo_desconhecido"] = True
    assert client.post("/relatos", json=dados).status_code == 422
    del dados["campo_desconhecido"]
    dados["localizacao"]["altura"] = 10
    assert client.post("/relatos", json=dados).status_code == 422


def test_classificacao(client, dados):
    relato_id = client.post("/relatos", json=dados).json()["id"]
    classificacao = {"categoria": "Iluminação", "prioridade": "Média",
                     "setor": "Iluminação Pública",
                     "risco_associado": "Baixa visibilidade durante a noite."}
    url = f"/relatos/{relato_id}/classificacao"
    resposta = client.put(url, json=classificacao)
    assert resposta.status_code == 200
    esperado = {**classificacao, "informacoes_relevantes": []}
    assert resposta.json()["classificacao"] == esperado
    assert resposta.json()["status"] == "Classificado"
    classificacao["prioridade"] = "Urgente"
    assert client.put(url, json=classificacao).status_code == 422
    assert client.get(f"/relatos/{relato_id}").json()["classificacao"] == esperado


def test_inexistente_e_uuid_invalido(client):
    assert client.get(f"/relatos/{uuid4()}").status_code == 404
    assert client.get("/relatos/id-invalido").status_code == 422
    dados = {"categoria": "Trânsito", "prioridade": "Alta", "setor": "Trânsito",
             "risco_associado": "Risco de acidente"}
    assert client.put(f"/relatos/{uuid4()}/classificacao", json=dados).status_code == 404


def test_instancias_isoladas(client, dados):
    client.post("/relatos", json=dados)
    with TestClient(criar_app()) as outro:
        assert outro.get("/relatos").json() == {"relatos": []}


def test_cors(client):
    resposta = client.options("/relatos", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://localhost:5173"
