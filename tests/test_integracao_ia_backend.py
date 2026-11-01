"""Integração ponta a ponta: ia/integrar_backend.py conversando com a API.

As chamadas HTTP do script (urlopen) são redirecionadas para o TestClient do
FastAPI, então o fluxo real é exercitado — GET /relatos, classificação,
PUT /relatos/{id}/classificacao — sem subir servidor e sem chamar o Groq.
"""
import io
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

import pytest

import integrar_backend

API_URL = "http://api-de-teste"


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@pytest.fixture
def api(client, monkeypatch):
    """Faz o urlopen do script falar com o TestClient."""
    def _urlopen(requisicao, timeout=None):
        caminho = urlsplit(requisicao.full_url).path
        resposta = client.request(requisicao.get_method(), caminho, content=requisicao.data,
                                  headers=dict(requisicao.header_items()))
        if resposta.status_code >= 400:
            raise HTTPError(requisicao.full_url, resposta.status_code, "erro", {},
                            io.BytesIO(resposta.content))
        return _Resposta(resposta.content)

    monkeypatch.setattr(integrar_backend, "urlopen", _urlopen)
    return client


def _classificador_por_palavra(texto):
    """Classificador determinístico usado no lugar da IA."""
    if "buraco" in texto.lower():
        return {"categoria": "Infraestrutura", "prioridade": "Alta", "setor": "Obras Viárias",
                "risco_associado": "Risco de acidente.", "informacoes_relevantes": []}
    return {"categoria": "Iluminação", "prioridade": "Média", "setor": "Iluminação Pública",
            "risco_associado": "Baixa visibilidade.", "informacoes_relevantes": []}


def test_classifica_todos_os_pendentes(api, criar_relato, monkeypatch):
    monkeypatch.setattr(integrar_backend, "classificar_relato", _classificador_por_palavra)
    buraco = criar_relato(texto="Buraco enorme na Avenida Vitória")
    poste = criar_relato(texto="Poste apagado na Rua da Lama")

    falhas = integrar_backend.classificar_pendentes(API_URL)

    assert falhas == 0
    relatos = {r["id"]: r for r in api.get("/relatos").json()["relatos"]}
    assert relatos[buraco["id"]]["status"] == "Classificado"
    assert relatos[buraco["id"]]["classificacao"]["categoria"] == "Infraestrutura"
    assert relatos[poste["id"]]["classificacao"]["prioridade"] == "Média"


def test_ignora_relatos_ja_classificados(api, criar_relato, classificacao_valida, monkeypatch):
    chamadas = []
    monkeypatch.setattr(integrar_backend, "classificar_relato",
                        lambda t: chamadas.append(t) or _classificador_por_palavra(t))
    ja_feito = criar_relato(texto="Relato que já foi classificado")
    api.put(f"/relatos/{ja_feito['id']}/classificacao", json=classificacao_valida)
    criar_relato(texto="Relato ainda pendente de análise")

    integrar_backend.classificar_pendentes(API_URL)
    assert chamadas == ["Relato ainda pendente de análise"]


def test_sem_pendentes(api, monkeypatch, capsys):
    monkeypatch.setattr(integrar_backend, "classificar_relato", _classificador_por_palavra)
    assert integrar_backend.classificar_pendentes(API_URL) == 0
    assert "Nenhum relato pendente" in capsys.readouterr().out


def test_relato_especifico_por_id(api, criar_relato, monkeypatch):
    monkeypatch.setattr(integrar_backend, "classificar_relato", _classificador_por_palavra)
    alvo = criar_relato(texto="Buraco na rua lateral da escola")
    outro = criar_relato(texto="Poste apagado perto da praça")

    integrar_backend.classificar_pendentes(API_URL, relato_id=alvo["id"])
    assert api.get(f"/relatos/{alvo['id']}").json()["status"] == "Classificado"
    assert api.get(f"/relatos/{outro['id']}").json()["status"] == "Recebido"


def test_falha_da_ia_conta_e_nao_interrompe_os_demais(api, criar_relato, monkeypatch):
    def classificador(texto):
        if "falha" in texto:
            raise integrar_backend.ErroIA("Limite de uso do Groq atingido.")
        return _classificador_por_palavra(texto)

    monkeypatch.setattr(integrar_backend, "classificar_relato", classificador)
    com_falha = criar_relato(texto="Este relato vai gerar falha")
    ok = criar_relato(texto="Buraco que deve ser classificado")

    assert integrar_backend.classificar_pendentes(API_URL) == 1
    assert api.get(f"/relatos/{com_falha['id']}").json()["status"] == "Recebido"
    assert api.get(f"/relatos/{ok['id']}").json()["status"] == "Classificado"


def test_classificacao_rejeitada_pela_api_conta_como_falha(api, criar_relato, monkeypatch):
    """Se a IA devolver algo fora do contrato, o backend responde 422 e o relato fica intacto."""
    monkeypatch.setattr(integrar_backend, "classificar_relato",
                        lambda t: {"categoria": "Saneamento", "prioridade": "Alta",
                                   "setor": "x", "risco_associado": "y"})
    relato = criar_relato()
    assert integrar_backend.classificar_pendentes(API_URL) == 1
    assert api.get(f"/relatos/{relato['id']}").json()["status"] == "Recebido"


def test_api_inacessivel_gera_runtime_error(monkeypatch):
    def _sem_rede(requisicao, timeout=None):
        raise URLError("connection refused")
    monkeypatch.setattr(integrar_backend, "urlopen", _sem_rede)
    with pytest.raises(RuntimeError, match="Não foi possível acessar a API"):
        integrar_backend.classificar_pendentes(API_URL)


def test_main_retorna_codigo_de_saida(api, criar_relato, monkeypatch):
    monkeypatch.setattr(integrar_backend, "classificar_relato", _classificador_por_palavra)
    criar_relato()
    monkeypatch.setattr("sys.argv", ["integrar_backend.py", "--api-url", API_URL])
    with pytest.raises(SystemExit) as saida:
        integrar_backend.main()
    assert saida.value.code == 0


def test_main_com_api_fora_do_ar_sai_com_erro(monkeypatch, capsys):
    monkeypatch.setattr(integrar_backend, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(URLError("refused")))
    monkeypatch.setattr("sys.argv", ["integrar_backend.py", "--api-url", API_URL])
    with pytest.raises(SystemExit) as saida:
        integrar_backend.main()
    assert saida.value.code == 1
    assert "Erro:" in capsys.readouterr().err


def test_fluxo_com_ia_em_modo_mock(api, criar_relato, monkeypatch):
    """Usa o classificar_relato verdadeiro do UrbanIA em modo mock."""
    import UrbanIA
    monkeypatch.setattr(UrbanIA, "USE_MOCK", True)
    monkeypatch.setattr(integrar_backend, "classificar_relato", UrbanIA.classificar_relato)
    relato = criar_relato()

    assert integrar_backend.classificar_pendentes(API_URL) == 0
    assert api.get(f"/relatos/{relato['id']}").json()["classificacao"] == UrbanIA.MOCK_CLASSIFICACAO
