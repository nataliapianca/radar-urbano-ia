"""Testes do harness de eval: dataset, métricas e geração do relatório."""
import csv
import json

import pytest

import metricas
import rodar_eval
from app.schemas.relatos import RelatoCriar


# --------------------------------------------------------------------------- #
# Dataset
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def dataset():
    return rodar_eval.carregar_dataset()


def test_dataset_valido_e_com_todas_as_classes(dataset):
    casos = dataset["casos"]
    assert len(casos) >= 30
    assert {c["categoria_esperada"] for c in casos} == set(metricas.CATEGORIAS)
    assert {c["prioridade_esperada"] for c in casos} == set(metricas.PRIORIDADES)
    assert {c["dificuldade"] for c in casos} <= {"clara", "ambígua"}


def test_relatos_do_dataset_sao_aceitos_pela_api(dataset):
    for caso in dataset["casos"]:
        RelatoCriar(texto=caso["texto"], localizacao={"latitude": 0, "longitude": 0})


@pytest.mark.parametrize("alteracao,mensagem", [
    ({"categoria_esperada": "Saneamento"}, "categoria inválida"),
    ({"prioridade_esperada": "Urgente"}, "prioridade inválida"),
    ({"texto": "curto"}, "texto fora do limite"),
])
def test_validacao_do_dataset_detecta_gabarito_errado(alteracao, mensagem):
    caso = {"id": "X1", "texto": "Relato de exemplo válido", "categoria_esperada": "Trânsito",
            "prioridade_esperada": "Alta", **alteracao}
    with pytest.raises(ValueError, match=mensagem):
        rodar_eval.validar_dataset([caso])


def test_validacao_do_dataset_detecta_id_duplicado():
    caso = {"id": "X1", "texto": "Relato de exemplo válido", "categoria_esperada": "Trânsito",
            "prioridade_esperada": "Alta"}
    with pytest.raises(ValueError, match="duplicados"):
        rodar_eval.validar_dataset([caso, dict(caso)])


# --------------------------------------------------------------------------- #
# Métricas
# --------------------------------------------------------------------------- #
def test_acuracia_conta_falha_como_erro():
    assert metricas.acuracia(["A", "B", "C", "D"], ["A", "B", "X", None]) == 0.5
    assert metricas.acuracia([], []) == 0.0


def test_precisao_revocacao_f1_com_valores_conhecidos():
    esperados = ["Alta", "Alta", "Média", "Baixa"]
    previstos = ["Alta", "Média", "Média", "Média"]
    por_classe = metricas.metricas_por_classe(esperados, previstos, metricas.PRIORIDADES)
    assert por_classe["Alta"] == {"precisao": 1.0, "revocacao": 0.5, "f1": pytest.approx(2 / 3),
                                  "suporte": 2}
    assert por_classe["Média"]["precisao"] == pytest.approx(1 / 3)
    assert por_classe["Média"]["revocacao"] == 1.0
    assert por_classe["Baixa"]["f1"] == 0.0
    assert metricas.f1_macro(por_classe) == pytest.approx((2 / 3 + 0.5 + 0) / 3)


def test_matriz_de_confusao_inclui_falhas():
    matriz = metricas.matriz_confusao(["Alta", "Alta", "Baixa"], ["Alta", None, "Alta"],
                                      metricas.PRIORIDADES)
    assert matriz["Alta"]["Alta"] == 1
    assert matriz["Alta"][metricas.FALHA] == 1
    assert matriz["Baixa"]["Alta"] == 1
    assert sum(sum(linha.values()) for linha in matriz.values()) == 3


def test_direcao_dos_erros_de_prioridade():
    erros = metricas.erros_de_prioridade(
        ["Alta", "Alta", "Alta", "Média", "Baixa"],
        ["Alta", "Baixa", None, "Alta", "Baixa"])
    assert erros["subestimadas"] == 1
    assert erros["superestimadas"] == 1
    assert erros["criticos_alta_como_baixa"] == 1
    assert erros["alta_perdida"] == 2           # Baixa + Falha
    assert erros["revocacao_alta"] == pytest.approx(1 / 3)
    assert erros["distancia_media"] == pytest.approx((0 + 2 + 1 + 0) / 4)


def test_percentil():
    assert metricas.percentil([1, 2, 3, 4, 5], 50) == 3
    assert metricas.percentil([1, 2, 3, 4, 5], 100) == 5
    assert metricas.percentil([10], 95) == 10
    assert metricas.percentil([], 95) == 0.0


# --------------------------------------------------------------------------- #
# Harness ponta a ponta (com classificador falso)
# --------------------------------------------------------------------------- #
CASOS = [
    {"id": "A", "texto": "Buraco grande na avenida", "categoria_esperada": "Infraestrutura",
     "prioridade_esperada": "Alta", "dificuldade": "clara"},
    {"id": "B", "texto": "Poste apagado há dias", "categoria_esperada": "Iluminação",
     "prioridade_esperada": "Média", "dificuldade": "clara"},
    {"id": "C", "texto": "Pichação no muro da escola", "categoria_esperada": "Limpeza Urbana",
     "prioridade_esperada": "Baixa", "dificuldade": "ambígua"},
    {"id": "D", "texto": "Relato que vai falhar na IA", "categoria_esperada": "Trânsito",
     "prioridade_esperada": "Alta", "dificuldade": "clara"},
]

RESPOSTAS = {
    "Buraco grande na avenida": {"categoria": "Infraestrutura", "prioridade": "Alta",
                                 "setor": "Obras", "risco_associado": "Acidente",
                                 "informacoes_relevantes": []},
    "Poste apagado há dias": {"categoria": "Iluminação", "prioridade": "Baixa",
                              "setor": "Iluminação Pública", "risco_associado": "Escuro",
                              "informacoes_relevantes": []},
    # Resposta fora do contrato: o backend deve rejeitar
    "Pichação no muro da escola": {"categoria": "Segurança", "prioridade": "Baixa",
                                   "setor": "", "risco_associado": "Nenhum"},
}


class ErroFalso(Exception):
    pass


def _classificador_falso(texto):
    if texto not in RESPOSTAS:
        raise ErroFalso("Limite de uso do Groq atingido.")
    return RESPOSTAS[texto]


@pytest.fixture
def resultados():
    return rodar_eval.avaliar(CASOS, _classificador_falso, ErroFalso,
                              rodar_eval.criar_verificador_contrato())


def test_avaliar_compara_esperado_e_previsto(resultados):
    por_id = {r["id"]: r for r in resultados}
    assert por_id["A"]["acertou_categoria"] and por_id["A"]["acertou_prioridade"]
    assert por_id["B"]["acertou_categoria"] and not por_id["B"]["acertou_prioridade"]
    assert not por_id["C"]["acertou_categoria"] and por_id["C"]["acertou_prioridade"]
    assert por_id["D"]["erro"] == "Limite de uso do Groq atingido."
    assert por_id["D"]["categoria_prevista"] is None


def test_avaliar_checa_contrato_no_backend(resultados):
    por_id = {r["id"]: r for r in resultados}
    assert por_id["A"]["aceito_backend"] is True
    assert por_id["C"]["aceito_backend"] is False  # setor vazio -> 422
    assert por_id["D"]["aceito_backend"] is None   # sem resposta, nada a enviar


def test_metricas_consolidadas(resultados):
    m = metricas.calcular_metricas(resultados)
    assert m["total_casos"] == 4
    assert m["acuracia_categoria"] == 0.5
    assert m["acuracia_prioridade"] == 0.5
    assert m["acuracia_ambos"] == 0.25
    assert m["falhas_ia"] == 1
    assert m["conformidade_contrato"] == pytest.approx(2 / 3)
    assert m["erros_prioridade"]["subestimadas"] == 1
    assert m["por_dificuldade"]["ambígua"]["casos"] == 1


def test_salvar_gera_relatorio_csv_json_e_historico(resultados, tmp_path):
    execucao = {"data": "2026-11-01T17:00:00", "modo": "groq", "rotulo": "teste",
                "modelo": "modelo-falso", "dataset": "x.json", "versao_dataset": "1.0", "casos": 4}
    m = metricas.calcular_metricas(resultados)
    pasta = rodar_eval.salvar_resultados(execucao, m, resultados, tmp_path)
    rodar_eval.salvar_resultados(execucao, m, resultados, tmp_path)  # segunda execução

    relatorio = (pasta / "relatorio.md").read_text(encoding="utf-8")
    assert "Acurácia de categoria | 50.0% (2/4)" in relatorio
    assert "Matriz de confusão" in relatorio
    assert "| B |" in relatorio and "Média → Baixa ❌" in relatorio
    assert "| A |" not in relatorio  # caso 100% certo não aparece nos divergentes

    salvo = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
    assert salvo["metricas"]["acuracia_ambos"] == 0.25
    assert len(salvo["casos"]) == 4

    with open(pasta / "casos.csv", encoding="utf-8-sig") as arquivo:
        assert len(list(csv.DictReader(arquivo, delimiter=";"))) == 4
    with open(tmp_path / "historico.csv", encoding="utf-8-sig") as arquivo:
        assert len(list(csv.DictReader(arquivo, delimiter=";"))) == 2


def test_modo_arquivo_reaproveita_respostas(resultados, tmp_path):
    execucao = {"data": "2026-11-01T17:00:00", "modo": "groq", "rotulo": "", "modelo": "m",
                "dataset": "x.json", "versao_dataset": "1.0", "casos": 4}
    pasta = rodar_eval.salvar_resultados(execucao, metricas.calcular_metricas(resultados),
                                         resultados, tmp_path)
    classificar, erro, modelo, latencias = rodar_eval.classificador_de_arquivo(pasta / "resultado.json")
    reprocessados = rodar_eval.avaliar(CASOS, classificar, erro, latencias_fixas=latencias)

    assert [r["categoria_prevista"] for r in reprocessados] == \
           [r["categoria_prevista"] for r in resultados]
    assert reprocessados[3]["erro"] == "Limite de uso do Groq atingido."
    assert modelo == "m (reprocessado)"


def test_linha_de_comando_em_modo_mock(tmp_path, capsys):
    codigo = rodar_eval.main(["--modo", "mock", "--limite", "5", "--saida", str(tmp_path)])
    assert codigo == 0
    pastas = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(pastas) == 1
    relatorio = (pastas[0] / "relatorio.md").read_text(encoding="utf-8")
    assert "modo mock" in relatorio
    assert "Relatório salvo em" in capsys.readouterr().out


def test_min_acuracia_falha_quando_abaixo(tmp_path):
    assert rodar_eval.main(["--modo", "mock", "--limite", "5", "--saida", str(tmp_path),
                            "--min-acuracia", "0.99"]) == 1
