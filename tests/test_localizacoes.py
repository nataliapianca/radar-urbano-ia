"""Busca de endereço (POST /localizacoes/buscar) e módulo de geocodificação.

O Geoapify nunca é chamado de verdade: substituímos `urlopen` por um dublê.
"""
import io
import json
from urllib.error import HTTPError, URLError

import pytest

from app import geocodificacao


class _RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _resposta_geoapify(resultados):
    return _RespostaFalsa(json.dumps({"results": resultados}).encode("utf-8"))


@pytest.fixture
def com_chave(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "chave-de-teste")


@pytest.fixture
def urlopen_falso(monkeypatch):
    """Substitui urlopen e guarda as requisições feitas."""
    chamadas = []

    def instalar(resposta=None, erro=None):
        def _urlopen(requisicao, timeout=None):
            chamadas.append(requisicao)
            if erro:
                raise erro
            return resposta
        monkeypatch.setattr(geocodificacao, "urlopen", _urlopen)
        return chamadas
    return instalar


# --------------------------------------------------------------------------- #
# Rota
# --------------------------------------------------------------------------- #
def test_sem_chave_retorna_503_com_orientacao(client):
    resposta = client.post("/localizacoes/buscar", json={"endereco": "Rua Sete, Vitória"})
    assert resposta.status_code == 503
    assert "GEOAPIFY_API_KEY" in resposta.json()["detail"]


@pytest.mark.parametrize("corpo", [
    {"endereco": "Rua"},               # menos de 5 caracteres
    {"endereco": "   Rua    "},        # 3 caracteres após strip
    {"endereco": "x" * 301},
    {},
    {"endereco": "Rua Sete, Vitória", "cidade": "Vitória"},  # campo extra
])
def test_busca_valida_entrada_antes_de_chamar_servico(client, com_chave, urlopen_falso, corpo):
    chamadas = urlopen_falso(resposta=_resposta_geoapify([]))
    assert client.post("/localizacoes/buscar", json=corpo).status_code == 422
    assert chamadas == []


def test_busca_retorna_opcoes_normalizadas(client, com_chave, urlopen_falso):
    urlopen_falso(resposta=_resposta_geoapify([
        {"lat": -20.32, "lon": -40.34, "formatted": "Rua Sete de Setembro, Vitória - ES",
         "datasource": {"attribution": "© OpenStreetMap contributors"}},
    ]))
    resposta = client.post("/localizacoes/buscar", json={"endereco": "Rua Sete de Setembro"})
    assert resposta.status_code == 200
    assert resposta.json() == {"resultados": [{
        "latitude": -20.32, "longitude": -40.34,
        "endereco": "Rua Sete de Setembro, Vitória - ES",
        "atribuicao": "© OpenStreetMap contributors",
    }]}


def test_servico_fora_do_ar_retorna_503(client, com_chave, urlopen_falso):
    urlopen_falso(erro=URLError("sem rede"))
    resposta = client.post("/localizacoes/buscar", json={"endereco": "Rua Sete de Setembro"})
    assert resposta.status_code == 503


# --------------------------------------------------------------------------- #
# Unidade: buscar_endereco
# --------------------------------------------------------------------------- #
def test_parametros_enviados_ao_geoapify(com_chave, urlopen_falso):
    chamadas = urlopen_falso(resposta=_resposta_geoapify([]))
    geocodificacao.buscar_endereco("Praia do Canto, Vitória")
    url = chamadas[0].full_url
    assert url.startswith("https://api.geoapify.com/v1/geocode/search?")
    assert "filter=countrycode%3Abr" in url
    assert "limit=3" in url
    assert "apiKey=chave-de-teste" in url


def test_resultados_invalidos_sao_descartados(com_chave, urlopen_falso):
    urlopen_falso(resposta=_resposta_geoapify([
        {"lat": -20.3, "lon": -40.3, "formatted": "Válido"},
        {"lat": "x", "lon": -40.3, "formatted": "Latitude inválida"},
        {"lon": -40.3, "formatted": "Sem latitude"},
        {"lat": 95, "lon": -40.3, "formatted": "Fora do intervalo"},
        {"lat": -20.3, "lon": -40.3, "formatted": "   "},
    ]))
    resultados = geocodificacao.buscar_endereco("Rua qualquer")
    assert [r["endereco"] for r in resultados] == ["Válido"]
    assert resultados[0]["atribuicao"] is None


def test_endereco_muito_longo_e_truncado(com_chave, urlopen_falso):
    urlopen_falso(resposta=_resposta_geoapify([
        {"lat": 0, "lon": 0, "formatted": "x" * 400, "datasource": {"attribution": "y" * 400}},
    ]))
    resultado = geocodificacao.buscar_endereco("Rua qualquer")[0]
    assert len(resultado["endereco"]) == 300
    assert len(resultado["atribuicao"]) == 300


@pytest.mark.parametrize("erro", [
    URLError("sem rede"),
    TimeoutError(),
    HTTPError("https://api.geoapify.com", 401, "Unauthorized", {}, None),
])
def test_falhas_de_rede_viram_erro_amigavel(com_chave, urlopen_falso, erro):
    urlopen_falso(erro=erro)
    with pytest.raises(geocodificacao.GeocodificacaoIndisponivel):
        geocodificacao.buscar_endereco("Rua qualquer")


def test_json_invalido_vira_erro_amigavel(com_chave, urlopen_falso):
    urlopen_falso(resposta=_RespostaFalsa(b"<html>erro</html>"))
    with pytest.raises(geocodificacao.GeocodificacaoIndisponivel):
        geocodificacao.buscar_endereco("Rua qualquer")
