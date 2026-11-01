"""Validação do cadastro de relatos (POST /relatos).

Cobre limites de tamanho, tipos, coordenadas, campos opcionais de
localização e rejeição de campos desconhecidos, conforme CONTRATO_API.md.
"""
from uuid import UUID

import pytest


# --------------------------------------------------------------------------- #
# Casos válidos
# --------------------------------------------------------------------------- #
def test_resposta_tem_formato_do_contrato(client, relato_valido):
    resposta = client.post("/relatos", json=relato_valido)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert set(corpo) == {"id", "texto", "localizacao", "status", "criado_em", "classificacao"}
    UUID(corpo["id"])  # lança ValueError se não for UUID
    assert corpo["status"] == "Recebido"
    assert corpo["classificacao"] is None
    assert corpo["localizacao"] == {**relato_valido["localizacao"],
                                    "endereco": None, "atribuicao": None}


def test_criado_em_esta_em_utc(client, relato_valido):
    criado_em = client.post("/relatos", json=relato_valido).json()["criado_em"]
    assert criado_em.endswith("Z") or criado_em.endswith("+00:00")


@pytest.mark.parametrize("tamanho", [10, 5000])
def test_texto_nos_limites_aceito(client, relato_valido, tamanho):
    relato_valido["texto"] = "a" * tamanho
    assert client.post("/relatos", json=relato_valido).status_code == 201


def test_limite_de_tamanho_considera_texto_sem_espacos_nas_pontas(client, relato_valido):
    # 9 caracteres úteis cercados de espaços: inválido mesmo com 29 no total
    relato_valido["texto"] = " " * 10 + "a" * 9 + " " * 10
    assert client.post("/relatos", json=relato_valido).status_code == 422
    relato_valido["texto"] = " " * 10 + "a" * 10 + " " * 10
    assert client.post("/relatos", json=relato_valido).json()["texto"] == "a" * 10


def test_texto_com_acentos_e_emojis_preservado(client, relato_valido):
    relato_valido["texto"] = "Árvore caída na calçada da Praça Costa Pereira 🌳⚠️"
    corpo = client.post("/relatos", json=relato_valido).json()
    assert corpo["texto"] == relato_valido["texto"]


@pytest.mark.parametrize("lat,lon", [(90, 180), (-90, -180), (0, 0)])
def test_coordenadas_nos_limites_aceitas(client, relato_valido, lat, lon):
    relato_valido["localizacao"] = {"latitude": lat, "longitude": lon}
    assert client.post("/relatos", json=relato_valido).status_code == 201


def test_endereco_e_atribuicao_opcionais_sao_guardados(client, relato_valido):
    relato_valido["localizacao"].update(
        endereco="Rua Sete de Setembro, Centro, Vitória - ES",
        atribuicao="© OpenStreetMap contributors",
    )
    corpo = client.post("/relatos", json=relato_valido).json()
    assert corpo["localizacao"]["endereco"] == "Rua Sete de Setembro, Centro, Vitória - ES"
    assert corpo["localizacao"]["atribuicao"] == "© OpenStreetMap contributors"


# --------------------------------------------------------------------------- #
# Casos inválidos -> HTTP 422 e nada é gravado
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("texto", ["a" * 9, "", "          ", "a" * 5001])
def test_texto_fora_dos_limites_rejeitado(client, relato_valido, texto):
    relato_valido["texto"] = texto
    assert client.post("/relatos", json=relato_valido).status_code == 422
    assert client.get("/relatos").json() == {"relatos": []}


@pytest.mark.parametrize("texto", [None, 12345678901, ["lista", "de", "textos"], {"a": 1}])
def test_texto_com_tipo_invalido_rejeitado(client, relato_valido, texto):
    relato_valido["texto"] = texto
    assert client.post("/relatos", json=relato_valido).status_code == 422


@pytest.mark.parametrize("campo,valor", [
    ("latitude", 90.0001), ("latitude", -90.0001),
    ("longitude", 180.0001), ("longitude", -180.0001),
    ("latitude", "abc"), ("longitude", None),
])
def test_coordenada_invalida_rejeitada(client, relato_valido, campo, valor):
    relato_valido["localizacao"][campo] = valor
    assert client.post("/relatos", json=relato_valido).status_code == 422


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-Infinity"])
def test_coordenada_nao_finita_rejeitada(client, relato_valido, valor):
    # JSON não tem NaN/Infinity; enviamos como string, que o Pydantic converteria
    # para float se allow_inf_nan não estivesse desligado.
    relato_valido["localizacao"]["latitude"] = valor
    assert client.post("/relatos", json=relato_valido).status_code == 422


@pytest.mark.parametrize("ausente", ["latitude", "longitude"])
def test_coordenada_obrigatoria(client, relato_valido, ausente):
    del relato_valido["localizacao"][ausente]
    assert client.post("/relatos", json=relato_valido).status_code == 422


@pytest.mark.parametrize("ausente", ["texto", "localizacao"])
def test_campos_raiz_obrigatorios(client, relato_valido, ausente):
    del relato_valido[ausente]
    assert client.post("/relatos", json=relato_valido).status_code == 422


def test_endereco_curto_demais_rejeitado(client, relato_valido):
    relato_valido["localizacao"]["endereco"] = "ab"
    assert client.post("/relatos", json=relato_valido).status_code == 422


def test_endereco_e_atribuicao_longos_demais_rejeitados(client, relato_valido):
    relato_valido["localizacao"]["endereco"] = "x" * 301
    assert client.post("/relatos", json=relato_valido).status_code == 422
    relato_valido["localizacao"]["endereco"] = None
    relato_valido["localizacao"]["atribuicao"] = "x" * 301
    assert client.post("/relatos", json=relato_valido).status_code == 422


@pytest.mark.parametrize("campo_proibido", ["id", "status", "criado_em", "classificacao"])
def test_cliente_nao_controla_campos_do_servidor(client, relato_valido, campo_proibido):
    """Status e classificação só podem mudar pelo fluxo da API, não no cadastro."""
    relato_valido[campo_proibido] = "Classificado"
    assert client.post("/relatos", json=relato_valido).status_code == 422


def test_corpo_que_nao_e_json_rejeitado(client):
    resposta = client.post("/relatos", content="texto puro",
                           headers={"Content-Type": "text/plain"})
    assert resposta.status_code == 422


def test_resposta_422_explica_o_campo_invalido(client, relato_valido):
    relato_valido["texto"] = "curto"
    detalhe = client.post("/relatos", json=relato_valido).json()["detail"]
    assert any(erro["loc"][-1] == "texto" for erro in detalhe)
