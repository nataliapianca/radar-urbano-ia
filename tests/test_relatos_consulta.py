"""Consulta de relatos (GET /relatos e GET /relatos/{id}) e rota de classificação
(PUT /relatos/{id}/classificacao)."""
from uuid import uuid4

import pytest


# --------------------------------------------------------------------------- #
# Consulta
# --------------------------------------------------------------------------- #
def test_health_check(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "online"


def test_lista_vazia(client):
    assert client.get("/relatos").json() == {"relatos": []}


def test_lista_mantem_ordem_de_cadastro(client, criar_relato):
    ids = [criar_relato(texto=f"Relato número {i} para teste de ordem")["id"] for i in range(5)]
    assert [r["id"] for r in client.get("/relatos").json()["relatos"]] == ids


def test_busca_por_id_devolve_o_relato_certo(client, criar_relato):
    primeiro = criar_relato(texto="Primeiro relato da sequência")
    segundo = criar_relato(texto="Segundo relato da sequência")
    assert client.get(f"/relatos/{segundo['id']}").json() == segundo
    assert client.get(f"/relatos/{primeiro['id']}").json() == primeiro


def test_id_inexistente_retorna_404_com_mensagem(client, criar_relato):
    criar_relato()
    resposta = client.get(f"/relatos/{uuid4()}")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Relato não encontrado"}


@pytest.mark.parametrize("id_invalido", ["123", "id-invalido", "00000000-0000-0000-0000"])
def test_id_fora_do_formato_uuid_retorna_422(client, id_invalido):
    assert client.get(f"/relatos/{id_invalido}").status_code == 422


def test_metodo_nao_permitido(client, criar_relato):
    relato = criar_relato()
    assert client.delete(f"/relatos/{relato['id']}").status_code == 405


# --------------------------------------------------------------------------- #
# Classificação
# --------------------------------------------------------------------------- #
def _url(relato_id):
    return f"/relatos/{relato_id}/classificacao"


def test_classificacao_muda_status_e_aparece_na_consulta(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    resposta = client.put(_url(relato["id"]), json=classificacao_valida)

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "Classificado"
    assert resposta.json()["classificacao"] == classificacao_valida
    # A classificação persiste na consulta individual e na listagem
    assert client.get(f"/relatos/{relato['id']}").json() == resposta.json()
    assert client.get("/relatos").json()["relatos"] == [resposta.json()]


def test_classificacao_nao_altera_texto_localizacao_nem_data(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    atualizado = client.put(_url(relato["id"]), json=classificacao_valida).json()
    for campo in ("id", "texto", "localizacao", "criado_em"):
        assert atualizado[campo] == relato[campo]


def test_reclassificar_substitui_a_anterior(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    client.put(_url(relato["id"]), json=classificacao_valida)
    nova = {**classificacao_valida, "categoria": "Segurança", "prioridade": "Alta",
            "informacoes_relevantes": []}
    resposta = client.put(_url(relato["id"]), json=nova)
    assert resposta.json()["classificacao"] == nova
    assert resposta.json()["status"] == "Classificado"


def test_classificar_um_relato_nao_afeta_outro(client, criar_relato, classificacao_valida):
    alvo, outro = criar_relato(), criar_relato()
    client.put(_url(alvo["id"]), json=classificacao_valida)
    assert client.get(f"/relatos/{outro['id']}").json() == outro


@pytest.mark.parametrize("categoria", ["Infraestrutura", "Iluminação", "Limpeza Urbana",
                                       "Trânsito", "Segurança", "Meio Ambiente"])
def test_todas_as_categorias_do_contrato_aceitas(client, criar_relato, classificacao_valida, categoria):
    relato = criar_relato()
    classificacao_valida["categoria"] = categoria
    assert client.put(_url(relato["id"]), json=classificacao_valida).status_code == 200


@pytest.mark.parametrize("prioridade", ["Alta", "Média", "Baixa"])
def test_todas_as_prioridades_do_contrato_aceitas(client, criar_relato, classificacao_valida, prioridade):
    relato = criar_relato()
    classificacao_valida["prioridade"] = prioridade
    assert client.put(_url(relato["id"]), json=classificacao_valida).status_code == 200


@pytest.mark.parametrize("campo,valor", [
    ("categoria", "Saneamento"),          # fora da lista
    ("categoria", "iluminação"),          # caixa diferente
    ("categoria", "Iluminacao"),          # sem acento
    ("prioridade", "Media"),              # sem acento
    ("prioridade", "Urgente"),
    ("setor", ""),
    ("setor", "   "),                     # vira vazio após strip
    ("setor", "x" * 151),
    ("risco_associado", ""),
    ("risco_associado", "x" * 1001),
    ("informacoes_relevantes", ["item"] * 21),
    ("informacoes_relevantes", "não é lista"),
])
def test_classificacao_invalida_rejeitada_sem_alterar_relato(
        client, criar_relato, classificacao_valida, campo, valor):
    relato = criar_relato()
    classificacao_valida[campo] = valor
    assert client.put(_url(relato["id"]), json=classificacao_valida).status_code == 422
    # "Uma classificação inválida não altera o relato existente" (contrato)
    assert client.get(f"/relatos/{relato['id']}").json() == relato


@pytest.mark.parametrize("ausente", ["categoria", "prioridade", "setor", "risco_associado"])
def test_campos_obrigatorios_da_classificacao(client, criar_relato, classificacao_valida, ausente):
    relato = criar_relato()
    del classificacao_valida[ausente]
    assert client.put(_url(relato["id"]), json=classificacao_valida).status_code == 422


def test_informacoes_relevantes_opcional_vira_lista_vazia(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    del classificacao_valida["informacoes_relevantes"]
    corpo = client.put(_url(relato["id"]), json=classificacao_valida).json()
    assert corpo["classificacao"]["informacoes_relevantes"] == []


def test_classificacao_com_campo_extra_rejeitada(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    classificacao_valida["confianca"] = 0.9
    assert client.put(_url(relato["id"]), json=classificacao_valida).status_code == 422


def test_classificacao_remove_espacos_das_pontas(client, criar_relato, classificacao_valida):
    relato = criar_relato()
    classificacao_valida["setor"] = "  Iluminação Pública  "
    corpo = client.put(_url(relato["id"]), json=classificacao_valida).json()
    assert corpo["classificacao"]["setor"] == "Iluminação Pública"


def test_classificar_relato_inexistente_retorna_404(client, classificacao_valida):
    assert client.put(_url(uuid4()), json=classificacao_valida).status_code == 404


def test_classificar_com_id_invalido_retorna_422(client, classificacao_valida):
    assert client.put(_url("nao-e-uuid"), json=classificacao_valida).status_code == 422
