"""Harness de avaliação (eval) da classificação da IA do Radar Urbano IA.

Roda cada relato do dataset pela IA, compara categoria/prioridade previstas
com as esperadas, mede latência, verifica se o backend aceita a resposta
(contrato da API) e salva um relatório para a apresentação.

Exemplos (a partir da raiz do repositório):

    python eval/rodar_eval.py --modo groq                  # IA real (precisa de GROQ_API_KEY)
    python eval/rodar_eval.py --modo groq --rotulo "prompt v2" --pausa 2
    python eval/rodar_eval.py --modo mock                  # teste do harness, sem Groq
    python eval/rodar_eval.py --modo arquivo --entrada eval/resultados/<pasta>/resultado.json

Saída: eval/resultados/<data>_<modo>/ com relatorio.md, resultado.json e
casos.csv, e uma linha nova em eval/resultados/historico.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent
PASTA_EVAL = Path(__file__).resolve().parent
for caminho in (RAIZ / "backend", RAIZ / "ia", PASTA_EVAL):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from metricas import CATEGORIAS, FALHA, PRIORIDADES, calcular_metricas  # noqa: E402

DATASET_PADRAO = PASTA_EVAL / "dataset" / "relatos_eval.json"
PASTA_RESULTADOS = PASTA_EVAL / "resultados"
LOCALIZACAO_TESTE = {"latitude": -20.3155, "longitude": -40.3128}

Classificador = Callable[[str], dict]


# --------------------------------------------------------------------------- #
# Dataset
# --------------------------------------------------------------------------- #
def carregar_dataset(caminho: Path = DATASET_PADRAO) -> dict:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    validar_dataset(dados["casos"])
    return dados


def validar_dataset(casos: list[dict]) -> None:
    """Garante que o gabarito usa apenas valores do contrato da API."""
    ids = [c["id"] for c in casos]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs duplicados no dataset")
    for caso in casos:
        if caso["categoria_esperada"] not in CATEGORIAS:
            raise ValueError(f"{caso['id']}: categoria inválida {caso['categoria_esperada']!r}")
        if caso["prioridade_esperada"] not in PRIORIDADES:
            raise ValueError(f"{caso['id']}: prioridade inválida {caso['prioridade_esperada']!r}")
        if not 10 <= len(caso["texto"].strip()) <= 5000:
            raise ValueError(f"{caso['id']}: texto fora do limite de 10 a 5000 caracteres")


# --------------------------------------------------------------------------- #
# Classificadores
# --------------------------------------------------------------------------- #
def carregar_classificador(modo: str) -> tuple[Classificador, type[Exception], str]:
    """Importa o UrbanIA no modo pedido e devolve (função, exceção, modelo)."""
    # O UrbanIA lê USE_MOCK no import; load_dotenv não sobrescreve o que já
    # está definido aqui, então o modo escolhido na linha de comando prevalece.
    os.environ["USE_MOCK"] = "true" if modo == "mock" else "false"
    if modo == "groq":
        from dotenv import load_dotenv
        load_dotenv(RAIZ / "ia" / ".env")
        if not os.getenv("GROQ_API_KEY"):
            sys.exit("GROQ_API_KEY não definida. Crie ia/.env ou use --modo mock.")
    import UrbanIA
    modelo = "mock (resposta fixa)" if modo == "mock" else UrbanIA.MODELO
    return UrbanIA.classificar_relato, UrbanIA.ErroIA, modelo


def classificador_de_arquivo(caminho: Path) -> tuple[Classificador, type[Exception], str, dict]:
    """Reaproveita as respostas de uma execução anterior (sem chamar a IA).

    Útil para recalcular métricas depois de corrigir o gabarito, ou para
    gravar o vídeo sem gastar cota do Groq.
    """
    with open(caminho, encoding="utf-8") as arquivo:
        anterior = json.load(arquivo)
    por_texto = {c["texto"]: c for c in anterior["casos"]}

    class RespostaAusente(Exception):
        pass

    def classificar(texto: str) -> dict:
        caso = por_texto.get(texto)
        if caso is None:
            raise RespostaAusente("relato não encontrado no arquivo de entrada")
        if caso.get("erro"):
            raise RespostaAusente(caso["erro"])
        return caso["resposta_ia"]

    latencias = {c["texto"]: c.get("latencia_s") for c in anterior["casos"]}
    modelo = anterior["execucao"].get("modelo", "desconhecido") + " (reprocessado)"
    return classificar, RespostaAusente, modelo, latencias


# --------------------------------------------------------------------------- #
# Avaliação
# --------------------------------------------------------------------------- #
def criar_verificador_contrato():
    """Envia a resposta da IA para a API real (em memória) e devolve o status HTTP.

    Assim o eval também mede se a IA respeita o contrato do backend: 200 =
    aceita; 422 = o backend rejeitaria a classificação.
    """
    from fastapi.testclient import TestClient
    from app.main import criar_app

    cliente = TestClient(criar_app())

    def verificar(texto: str, classificacao: dict) -> int:
        relato = cliente.post("/relatos", json={"texto": texto, "localizacao": LOCALIZACAO_TESTE})
        relato.raise_for_status()
        return cliente.put(f"/relatos/{relato.json()['id']}/classificacao",
                           json=classificacao).status_code

    return verificar


def avaliar(casos: list[dict], classificar: Classificador, erro_esperado: type[Exception],
            verificar_contrato=None, pausa: float = 0.0, latencias_fixas: dict | None = None,
            ao_avaliar: Callable[[int, dict], None] | None = None) -> list[dict]:
    """Classifica cada caso e registra esperado x previsto."""
    resultados = []
    for indice, caso in enumerate(casos, start=1):
        inicio = time.perf_counter()
        resposta, erro = None, None
        try:
            resposta = classificar(caso["texto"])
        except erro_esperado as excecao:
            erro = str(excecao) or excecao.__class__.__name__
        latencia = time.perf_counter() - inicio
        if latencias_fixas is not None:
            latencia = latencias_fixas.get(caso["texto"])

        aceito = None
        if resposta is not None and verificar_contrato is not None:
            aceito = verificar_contrato(caso["texto"], resposta) == 200

        categoria = resposta.get("categoria") if resposta else None
        prioridade = resposta.get("prioridade") if resposta else None
        resultado = {
            "id": caso["id"],
            "texto": caso["texto"],
            "dificuldade": caso.get("dificuldade", "—"),
            "categoria_esperada": caso["categoria_esperada"],
            "categoria_prevista": categoria,
            "acertou_categoria": categoria == caso["categoria_esperada"],
            "prioridade_esperada": caso["prioridade_esperada"],
            "prioridade_prevista": prioridade,
            "acertou_prioridade": prioridade == caso["prioridade_esperada"],
            "setor_previsto": resposta.get("setor") if resposta else None,
            "aceito_backend": aceito,
            "latencia_s": round(latencia, 3) if latencia is not None else None,
            "erro": erro,
            "resposta_ia": resposta,
        }
        resultados.append(resultado)
        if ao_avaliar:
            ao_avaliar(indice, resultado)
        if pausa and indice < len(casos):
            time.sleep(pausa)
    return resultados


# --------------------------------------------------------------------------- #
# Relatório
# --------------------------------------------------------------------------- #
def _pct(valor: float | None) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%"


def _tabela_matriz(matriz: dict[str, dict[str, int]]) -> list[str]:
    colunas = list(next(iter(matriz.values())))
    if not any(linha[FALHA] for linha in matriz.values()):
        colunas.remove(FALHA)
    linhas = ["| Esperado \\ Previsto | " + " | ".join(colunas) + " |",
              "|---|" + "---:|" * len(colunas)]
    for esperado, contagens in matriz.items():
        celulas = [f"**{contagens[c]}**" if c == esperado and contagens[c] else str(contagens[c])
                   for c in colunas]
        linhas.append(f"| {esperado} | " + " | ".join(celulas) + " |")
    return linhas


def _tabela_por_classe(por_classe: dict) -> list[str]:
    linhas = ["| Classe | Precisão | Revocação | F1 | Casos |", "|---|---:|---:|---:|---:|"]
    for rotulo, m in por_classe.items():
        linhas.append(f"| {rotulo} | {_pct(m['precisao'])} | {_pct(m['revocacao'])} | "
                      f"{_pct(m['f1'])} | {m['suporte']} |")
    return linhas


def gerar_relatorio_md(execucao: dict, metricas: dict, resultados: list[dict]) -> str:
    m = metricas
    ep = m["erros_prioridade"]
    n = m["total_casos"]
    linhas = [
        "# Relatório de avaliação da IA — Radar Urbano IA",
        "",
        f"- **Data:** {execucao['data']}",
        f"- **Modo:** {execucao['modo']}" + (f" · **Rótulo:** {execucao['rotulo']}" if execucao.get("rotulo") else ""),
        f"- **Modelo:** {execucao['modelo']}",
        f"- **Dataset:** `{execucao['dataset']}` (versão {execucao['versao_dataset']}, {n} relatos)",
        "",
    ]
    if execucao["modo"] == "mock":
        linhas += ["> ⚠️ Execução em **modo mock**: a IA devolve sempre a mesma resposta. "
                   "Serve só para validar o harness; as métricas abaixo **não** medem a IA real.", ""]
    linhas += [
        "## Resumo",
        "",
        "| Métrica | Resultado |",
        "|---|---:|",
        f"| Acurácia de categoria | {_pct(m['acuracia_categoria'])} ({m['acertos']['categoria']}/{n}) |",
        f"| Acurácia de prioridade | {_pct(m['acuracia_prioridade'])} ({m['acertos']['prioridade']}/{n}) |",
        f"| Acerto de categoria **e** prioridade | {_pct(m['acuracia_ambos'])} ({m['acertos']['ambos']}/{n}) |",
        f"| F1 macro — categoria | {_pct(m['f1_macro_categoria'])} |",
        f"| F1 macro — prioridade | {_pct(m['f1_macro_prioridade'])} |",
        f"| Revocação de prioridade Alta | {_pct(ep['revocacao_alta'])} "
        f"({ep['total_alta_esperada'] - ep['alta_perdida']}/{ep['total_alta_esperada']}) |",
        f"| Erros críticos (Alta classificada como Baixa) | {ep['criticos_alta_como_baixa']} |",
        f"| Respostas aceitas pelo backend (contrato) | {_pct(m['conformidade_contrato'])} |",
        f"| Falhas da IA (erro/timeout/formato) | {m['falhas_ia']} ({_pct(m['taxa_falha'])}) |",
        f"| Latência média / p95 | {m['latencia_s']['media']:.2f}s / {m['latencia_s']['p95']:.2f}s |",
        "",
        "## Por dificuldade do caso",
        "",
        "| Dificuldade | Casos | Acurácia categoria | Acurácia prioridade |",
        "|---|---:|---:|---:|",
    ]
    for nivel, d in m["por_dificuldade"].items():
        linhas.append(f"| {nivel} | {d['casos']} | {_pct(d['acuracia_categoria'])} | "
                      f"{_pct(d['acuracia_prioridade'])} |")
    linhas += ["", "## Categoria", "", "### Métricas por classe", ""]
    linhas += _tabela_por_classe(m["por_classe_categoria"])
    linhas += ["", "### Matriz de confusão", ""] + _tabela_matriz(m["matriz_categoria"])
    linhas += ["", "## Prioridade", "", "### Métricas por classe", ""]
    linhas += _tabela_por_classe(m["por_classe_prioridade"])
    linhas += ["", "### Matriz de confusão", ""] + _tabela_matriz(m["matriz_prioridade"])
    linhas += [
        "",
        "### Direção dos erros de prioridade",
        "",
        f"- Subestimadas (IA deu prioridade menor que a esperada): **{ep['subestimadas']}**",
        f"- Superestimadas (IA deu prioridade maior que a esperada): **{ep['superestimadas']}**",
        f"- Distância média entre níveis (0 = perfeito, 2 = pior): **{ep['distancia_media']:.2f}**",
        "",
        "## Casos divergentes",
        "",
    ]
    divergentes = [r for r in resultados if not (r["acertou_categoria"] and r["acertou_prioridade"])]
    if not divergentes:
        linhas.append("Nenhum — a IA acertou categoria e prioridade em todos os casos.")
    else:
        linhas += ["| ID | Relato | Categoria (esperada → IA) | Prioridade (esperada → IA) | Obs. |",
                   "|---|---|---|---|---|"]
        for r in divergentes:
            texto = r["texto"] if len(r["texto"]) <= 90 else r["texto"][:87] + "..."
            cat = (f"{r['categoria_esperada']} → {r['categoria_prevista'] or FALHA}"
                   + ("" if r["acertou_categoria"] else " ❌"))
            pri = (f"{r['prioridade_esperada']} → {r['prioridade_prevista'] or FALHA}"
                   + ("" if r["acertou_prioridade"] else " ❌"))
            obs = r["erro"] or ("ambígua" if r["dificuldade"] == "ambígua" else "")
            linhas.append(f"| {r['id']} | {texto.replace('|', '/')} | {cat} | {pri} | {obs} |")
    linhas += ["", "---", "Gerado por `eval/rodar_eval.py`. Detalhes de cada caso em `casos.csv` "
               "e `resultado.json`.", ""]
    return "\n".join(linhas)


def salvar_resultados(execucao: dict, metricas: dict, resultados: list[dict],
                      pasta_base: Path = PASTA_RESULTADOS) -> Path:
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    pasta = pasta_base / f"{carimbo}_{execucao['modo']}"
    pasta.mkdir(parents=True, exist_ok=True)

    with open(pasta / "resultado.json", "w", encoding="utf-8") as arquivo:
        json.dump({"execucao": execucao, "metricas": metricas, "casos": resultados},
                  arquivo, ensure_ascii=False, indent=2)

    colunas = ["id", "dificuldade", "categoria_esperada", "categoria_prevista", "acertou_categoria",
               "prioridade_esperada", "prioridade_prevista", "acertou_prioridade",
               "setor_previsto", "aceito_backend", "latencia_s", "erro", "texto"]
    with open(pasta / "casos.csv", "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore", delimiter=";")
        escritor.writeheader()
        escritor.writerows(resultados)

    (pasta / "relatorio.md").write_text(gerar_relatorio_md(execucao, metricas, resultados),
                                        encoding="utf-8")

    historico = pasta_base / "historico.csv"
    novo = not historico.exists()
    with open(historico, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        if novo:
            escritor.writerow(["data", "modo", "rotulo", "modelo", "casos", "acuracia_categoria",
                               "acuracia_prioridade", "acuracia_ambos", "f1_macro_categoria",
                               "f1_macro_prioridade", "revocacao_alta", "criticos",
                               "conformidade_contrato", "falhas", "latencia_media_s", "pasta"])
        escritor.writerow([
            execucao["data"], execucao["modo"], execucao.get("rotulo") or "", execucao["modelo"],
            metricas["total_casos"], f"{metricas['acuracia_categoria']:.4f}",
            f"{metricas['acuracia_prioridade']:.4f}", f"{metricas['acuracia_ambos']:.4f}",
            f"{metricas['f1_macro_categoria']:.4f}", f"{metricas['f1_macro_prioridade']:.4f}",
            f"{metricas['erros_prioridade']['revocacao_alta']:.4f}",
            metricas["erros_prioridade"]["criticos_alta_como_baixa"],
            "" if metricas["conformidade_contrato"] is None else f"{metricas['conformidade_contrato']:.4f}",
            metricas["falhas_ia"], f"{metricas['latencia_s']['media']:.3f}", pasta.name,
        ])
    return pasta


# --------------------------------------------------------------------------- #
# Linha de comando
# --------------------------------------------------------------------------- #
def _imprimir_progresso(total: int):
    def imprimir(indice: int, r: dict):
        if r["erro"]:
            situacao = f"FALHA: {r['erro']}"
        else:
            marca_cat = "✔" if r["acertou_categoria"] else "✘"
            marca_pri = "✔" if r["acertou_prioridade"] else "✘"
            situacao = (f"{marca_cat} {r['categoria_prevista']:<15} {marca_pri} "
                        f"{r['prioridade_prevista']:<6} ({r['latencia_s'] or 0:.2f}s)")
        print(f"[{indice:>2}/{total}] {r['id']:<5} {situacao}", flush=True)
    return imprimir


def main(argv=None) -> int:
    # Evita UnicodeEncodeError (✔/✘/acentos) quando a saída é redirecionada no Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Avalia a classificação da IA do Radar Urbano IA.")
    parser.add_argument("--modo", choices=["groq", "mock", "arquivo"], default="groq",
                        help="groq: IA real; mock: resposta fixa; arquivo: reprocessa um resultado.json")
    parser.add_argument("--dataset", type=Path, default=DATASET_PADRAO)
    parser.add_argument("--entrada", type=Path, help="resultado.json anterior (obrigatório no modo arquivo)")
    parser.add_argument("--limite", type=int, help="avalia apenas os N primeiros casos")
    parser.add_argument("--ids", help="avalia apenas os IDs informados, separados por vírgula")
    parser.add_argument("--pausa", type=float, default=0.0,
                        help="segundos de espera entre chamadas (ajuda com o limite do plano gratuito)")
    parser.add_argument("--rotulo", default="", help="descrição da execução, ex.: 'prompt v2'")
    parser.add_argument("--saida", type=Path, default=PASTA_RESULTADOS)
    parser.add_argument("--sem-contrato", action="store_true",
                        help="não envia as respostas ao backend para checar o contrato")
    parser.add_argument("--min-acuracia", type=float,
                        help="sai com código 1 se a acurácia de categoria ou prioridade ficar abaixo deste valor (0–1)")
    args = parser.parse_args(argv)

    dataset = carregar_dataset(args.dataset)
    casos = dataset["casos"]
    if args.ids:
        selecionados = {i.strip() for i in args.ids.split(",")}
        casos = [c for c in casos if c["id"] in selecionados]
    if args.limite:
        casos = casos[: args.limite]
    if not casos:
        parser.error("nenhum caso selecionado")

    latencias_fixas = None
    if args.modo == "arquivo":
        if not args.entrada:
            parser.error("--entrada é obrigatório no modo arquivo")
        classificar, erro, modelo, latencias_fixas = classificador_de_arquivo(args.entrada)
    else:
        classificar, erro, modelo = carregar_classificador(args.modo)

    try:
        dataset_rel = args.dataset.resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        dataset_rel = str(args.dataset)
    execucao = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "modo": args.modo,
        "rotulo": args.rotulo,
        "modelo": modelo,
        "dataset": dataset_rel,
        "versao_dataset": dataset.get("versao", "—"),
        "casos": len(casos),
    }

    print(f"Avaliando {len(casos)} relatos · modo={args.modo} · modelo={modelo}\n")
    verificador = None if args.sem_contrato else criar_verificador_contrato()
    resultados = avaliar(casos, classificar, erro, verificador, args.pausa,
                         latencias_fixas, _imprimir_progresso(len(casos)))
    metricas = calcular_metricas(resultados)
    pasta = salvar_resultados(execucao, metricas, resultados, args.saida)

    print("\n" + "=" * 60)
    print(f"Acurácia categoria : {_pct(metricas['acuracia_categoria'])}")
    print(f"Acurácia prioridade: {_pct(metricas['acuracia_prioridade'])}")
    print(f"Acerto dos dois    : {_pct(metricas['acuracia_ambos'])}")
    print(f"Revocação de Alta  : {_pct(metricas['erros_prioridade']['revocacao_alta'])}")
    print(f"Contrato backend   : {_pct(metricas['conformidade_contrato'])}")
    print(f"Falhas da IA       : {metricas['falhas_ia']}")
    print("=" * 60)
    print(f"Relatório salvo em: {pasta / 'relatorio.md'}")

    if args.min_acuracia is not None and min(metricas["acuracia_categoria"],
                                             metricas["acuracia_prioridade"]) < args.min_acuracia:
        print(f"Abaixo da acurácia mínima de {_pct(args.min_acuracia)}.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
