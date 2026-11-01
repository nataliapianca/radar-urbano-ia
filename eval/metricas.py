"""Métricas de acerto/erro da classificação da IA.

Implementadas em Python puro (sem scikit-learn) para manter o harness leve
e fácil de explicar na apresentação. Um caso em que a IA falhou (erro de
chamada ou resposta inválida) tem previsão ``None`` e conta como erro.
"""
from __future__ import annotations

from collections import Counter

CATEGORIAS = ["Infraestrutura", "Iluminação", "Limpeza Urbana",
              "Trânsito", "Segurança", "Meio Ambiente"]
PRIORIDADES = ["Alta", "Média", "Baixa"]
FALHA = "Falha"  # rótulo usado nas matrizes quando a IA não devolveu resposta

# Ordem de gravidade usada para medir sub/superestimação da prioridade
NIVEL_PRIORIDADE = {"Baixa": 0, "Média": 1, "Alta": 2}


def acuracia(esperados: list[str], previstos: list[str | None]) -> float:
    """Proporção de casos em que previsto == esperado (falhas contam como erro)."""
    if not esperados:
        return 0.0
    return sum(e == p for e, p in zip(esperados, previstos)) / len(esperados)


def matriz_confusao(esperados, previstos, rotulos) -> dict[str, dict[str, int]]:
    """matriz[esperado][previsto] = quantidade. Inclui a coluna 'Falha'."""
    colunas = list(rotulos) + [FALHA]
    matriz = {e: {p: 0 for p in colunas} for e in rotulos}
    for e, p in zip(esperados, previstos):
        matriz[e][p if p in colunas else FALHA] += 1
    return matriz


def metricas_por_classe(esperados, previstos, rotulos) -> dict[str, dict[str, float]]:
    """Precisão, revocação (recall), F1 e suporte de cada classe.

    - precisão: dos casos que a IA marcou como X, quantos eram X;
    - revocação: dos casos que eram X, quantos a IA marcou como X;
    - F1: média harmônica entre as duas.
    """
    resultado = {}
    for rotulo in rotulos:
        vp = sum(e == rotulo and p == rotulo for e, p in zip(esperados, previstos))
        fp = sum(e != rotulo and p == rotulo for e, p in zip(esperados, previstos))
        fn = sum(e == rotulo and p != rotulo for e, p in zip(esperados, previstos))
        precisao = vp / (vp + fp) if vp + fp else 0.0
        revocacao = vp / (vp + fn) if vp + fn else 0.0
        f1 = 2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0
        resultado[rotulo] = {"precisao": precisao, "revocacao": revocacao, "f1": f1,
                             "suporte": vp + fn}
    return resultado


def f1_macro(por_classe: dict[str, dict[str, float]]) -> float:
    """Média simples do F1 das classes que aparecem no conjunto esperado."""
    valores = [m["f1"] for m in por_classe.values() if m["suporte"] > 0]
    return sum(valores) / len(valores) if valores else 0.0


def erros_de_prioridade(esperados, previstos) -> dict[str, float | int]:
    """Direção do erro de prioridade.

    - subestimada: IA deu prioridade MENOR que a esperada (mais perigoso:
      um problema grave pode ficar no fim da fila);
    - superestimada: IA deu prioridade MAIOR que a esperada;
    - alta_perdida: esperado Alta e a IA não deu Alta;
    - critico: esperado Alta e a IA deu Baixa (erro de dois níveis);
    - distancia_media: média de |nível esperado - nível previsto| nos casos
      respondidos (0 = perfeito, 2 = pior caso).
    """
    sub = sup = alta_perdida = critico = 0
    distancias = []
    for e, p in zip(esperados, previstos):
        if e == "Alta" and p != "Alta":
            alta_perdida += 1
        if p not in NIVEL_PRIORIDADE:
            continue
        diferenca = NIVEL_PRIORIDADE[p] - NIVEL_PRIORIDADE[e]
        distancias.append(abs(diferenca))
        sub += diferenca < 0
        sup += diferenca > 0
        critico += e == "Alta" and p == "Baixa"
    total_alta = sum(e == "Alta" for e in esperados)
    return {
        "subestimadas": sub,
        "superestimadas": sup,
        "alta_perdida": alta_perdida,
        "total_alta_esperada": total_alta,
        "revocacao_alta": (total_alta - alta_perdida) / total_alta if total_alta else 0.0,
        "criticos_alta_como_baixa": critico,
        "distancia_media": sum(distancias) / len(distancias) if distancias else 0.0,
    }


def percentil(valores: list[float], p: float) -> float:
    """Percentil por interpolação linear (p entre 0 e 100)."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    posicao = (len(ordenados) - 1) * p / 100
    inferior = int(posicao)
    superior = min(inferior + 1, len(ordenados) - 1)
    return ordenados[inferior] + (ordenados[superior] - ordenados[inferior]) * (posicao - inferior)


def calcular_metricas(resultados: list[dict]) -> dict:
    """Consolida as métricas a partir da lista de casos avaliados.

    Cada item precisa de: categoria_esperada, prioridade_esperada,
    categoria_prevista, prioridade_prevista, erro, latencia_s, dificuldade
    e (opcional) aceito_backend.
    """
    cat_esp = [r["categoria_esperada"] for r in resultados]
    cat_prev = [r["categoria_prevista"] for r in resultados]
    pri_esp = [r["prioridade_esperada"] for r in resultados]
    pri_prev = [r["prioridade_prevista"] for r in resultados]

    por_classe_cat = metricas_por_classe(cat_esp, cat_prev, CATEGORIAS)
    por_classe_pri = metricas_por_classe(pri_esp, pri_prev, PRIORIDADES)
    latencias = [r["latencia_s"] for r in resultados if r.get("latencia_s") is not None]
    contrato = [r["aceito_backend"] for r in resultados if r.get("aceito_backend") is not None]

    por_dificuldade = {}
    for nivel, quantidade in sorted(Counter(r.get("dificuldade", "—") for r in resultados).items()):
        grupo = [r for r in resultados if r.get("dificuldade", "—") == nivel]
        por_dificuldade[nivel] = {
            "casos": quantidade,
            "acuracia_categoria": acuracia([r["categoria_esperada"] for r in grupo],
                                           [r["categoria_prevista"] for r in grupo]),
            "acuracia_prioridade": acuracia([r["prioridade_esperada"] for r in grupo],
                                            [r["prioridade_prevista"] for r in grupo]),
        }

    total = len(resultados)
    acertos_ambos = sum(r["categoria_prevista"] == r["categoria_esperada"]
                        and r["prioridade_prevista"] == r["prioridade_esperada"]
                        for r in resultados)
    falhas = sum(bool(r.get("erro")) for r in resultados)

    return {
        "total_casos": total,
        "falhas_ia": falhas,
        "taxa_falha": falhas / total if total else 0.0,
        "acuracia_categoria": acuracia(cat_esp, cat_prev),
        "acuracia_prioridade": acuracia(pri_esp, pri_prev),
        "acuracia_ambos": acertos_ambos / total if total else 0.0,
        "acertos": {"categoria": sum(e == p for e, p in zip(cat_esp, cat_prev)),
                    "prioridade": sum(e == p for e, p in zip(pri_esp, pri_prev)),
                    "ambos": acertos_ambos},
        "f1_macro_categoria": f1_macro(por_classe_cat),
        "f1_macro_prioridade": f1_macro(por_classe_pri),
        "por_classe_categoria": por_classe_cat,
        "por_classe_prioridade": por_classe_pri,
        "matriz_categoria": matriz_confusao(cat_esp, cat_prev, CATEGORIAS),
        "matriz_prioridade": matriz_confusao(pri_esp, pri_prev, PRIORIDADES),
        "erros_prioridade": erros_de_prioridade(pri_esp, pri_prev),
        "por_dificuldade": por_dificuldade,
        "conformidade_contrato": (sum(contrato) / len(contrato)) if contrato else None,
        "latencia_s": {
            "media": sum(latencias) / len(latencias) if latencias else 0.0,
            "mediana": percentil(latencias, 50),
            "p95": percentil(latencias, 95),
            "max": max(latencias) if latencias else 0.0,
        },
    }
