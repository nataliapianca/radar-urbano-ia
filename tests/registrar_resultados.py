"""Roda a suíte do pytest e registra os resultados para a apresentação.

Uso (a partir da raiz do repositório):

    python tests/registrar_resultados.py

Gera tests/resultados/<data>/ com:
- resumo.md   → tabela por arquivo de teste, totais, cobertura e falhas
- junit.xml   → relatório padrão JUnit (lido por CI/IDEs)
- saida.txt   → saída completa do pytest
e acrescenta uma linha em tests/resultados/historico.csv.

Se o pytest-cov estiver instalado (requirements-dev.txt), inclui a cobertura.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = RAIZ / "tests" / "resultados"

DESCRICOES = {
    "test_api": "Fluxo básico da API (cadastro, consulta, classificação, CORS)",
    "test_relatos_cadastro": "Validação do cadastro de relatos (POST /relatos)",
    "test_relatos_consulta": "Consulta de relatos e rota de classificação",
    "test_localizacoes": "Busca de endereço / geocodificação (Geoapify simulado)",
    "test_repositorio": "Repositório em memória (unidade)",
    "test_urbania": "Módulo de IA — prompt, schema, validação e erros (Groq simulado)",
    "test_integracao_ia_backend": "Integração IA → API (integrar_backend.py)",
    "test_eval": "Harness de eval — dataset, métricas e relatório",
}


def executar_pytest(pasta: Path, argumentos_extras: list[str]) -> tuple[int, str, float | None]:
    junit = pasta / "junit.xml"
    comando = [sys.executable, "-B", "-m", "pytest", "-v", "-p", "no:cacheprovider",
               f"--junitxml={junit}", "-o", "junit_family=xunit2"]
    cobertura_json = pasta / "cobertura.json"
    tem_cov = importlib.util.find_spec("pytest_cov") is not None
    if tem_cov:
        comando += ["--cov", "--cov-report=term", f"--cov-report=json:{cobertura_json}"]
    comando += argumentos_extras

    processo = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    saida = processo.stdout + processo.stderr
    (pasta / "saida.txt").write_text(saida, encoding="utf-8")

    cobertura = None
    if tem_cov and cobertura_json.exists():
        cobertura = json.loads(cobertura_json.read_text(encoding="utf-8"))["totals"]["percent_covered"]
    return processo.returncode, saida, cobertura


def ler_junit(caminho: Path) -> list[dict]:
    casos = []
    for caso in ET.parse(caminho).getroot().iter("testcase"):
        if caso.find("failure") is not None or caso.find("error") is not None:
            no = caso.find("failure") if caso.find("failure") is not None else caso.find("error")
            status, mensagem = "falhou", (no.get("message") or "").strip()
        elif caso.find("skipped") is not None:
            status, mensagem = "ignorado", (caso.find("skipped").get("message") or "")
        else:
            status, mensagem = "passou", ""
        modulo = caso.get("classname", "").split(".")[-1]
        casos.append({"modulo": modulo, "nome": caso.get("name", ""), "status": status,
                      "tempo": float(caso.get("time", 0) or 0), "mensagem": mensagem})
    return casos


def gerar_resumo(casos: list[dict], cobertura: float | None, data: str) -> str:
    por_modulo = defaultdict(lambda: {"passou": 0, "falhou": 0, "ignorado": 0, "tempo": 0.0})
    for caso in casos:
        por_modulo[caso["modulo"]][caso["status"]] += 1
        por_modulo[caso["modulo"]]["tempo"] += caso["tempo"]

    total = len(casos)
    passou = sum(c["status"] == "passou" for c in casos)
    falhou = sum(c["status"] == "falhou" for c in casos)
    tempo = sum(c["tempo"] for c in casos)
    situacao = "✅ Todos os testes passaram" if falhou == 0 else f"❌ {falhou} teste(s) falharam"

    linhas = [
        "# Resultado dos testes automatizados — Radar Urbano IA",
        "",
        f"- **Data:** {data}",
        f"- **Python:** {sys.version.split()[0]}",
        f"- **Situação:** {situacao}",
        f"- **Total:** {total} testes · {passou} passaram · {falhou} falharam · {tempo:.2f}s",
    ]
    if cobertura is not None:
        linhas.append(f"- **Cobertura de código:** {cobertura:.1f}% (backend/app, ia, eval; exceto ia/Chat.py)")
    linhas += ["", "## Por arquivo de teste", "",
               "| Arquivo | O que verifica | Passou | Falhou | Tempo |",
               "|---|---|---:|---:|---:|"]
    for modulo, r in sorted(por_modulo.items()):
        linhas.append(f"| `{modulo}.py` | {DESCRICOES.get(modulo, '')} | {r['passou']} | "
                      f"{r['falhou']} | {r['tempo']:.2f}s |")

    falhas = [c for c in casos if c["status"] == "falhou"]
    if falhas:
        linhas += ["", "## Falhas", ""]
        for c in falhas:
            linhas.append(f"- `{c['modulo']}::{c['nome']}` — {c['mensagem'][:200]}")

    linhas += ["", "## Lista completa", "", "<details><summary>Ver todos os testes</summary>", ""]
    for c in casos:
        marca = {"passou": "✅", "falhou": "❌", "ignorado": "⏭️"}[c["status"]]
        linhas.append(f"- {marca} `{c['modulo']}::{c['nome']}`")
    linhas += ["", "</details>", "", "---",
               "Gerado por `tests/registrar_resultados.py`. Saída completa em `saida.txt`.", ""]
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = datetime.now()
    pasta = PASTA_RESULTADOS / data.strftime("%Y%m%d-%H%M%S")
    pasta.mkdir(parents=True, exist_ok=True)

    print("Executando a suíte de testes...")
    codigo, saida, cobertura = executar_pytest(pasta, argv if argv is not None else sys.argv[1:])
    casos = ler_junit(pasta / "junit.xml")
    (pasta / "resumo.md").write_text(gerar_resumo(casos, cobertura, data.isoformat(timespec="seconds")),
                                     encoding="utf-8")

    historico = PASTA_RESULTADOS / "historico.csv"
    novo = not historico.exists()
    with open(historico, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        if novo:
            escritor.writerow(["data", "total", "passou", "falhou", "tempo_s", "cobertura_pct", "pasta"])
        escritor.writerow([
            data.isoformat(timespec="seconds"), len(casos),
            sum(c["status"] == "passou" for c in casos), sum(c["status"] == "falhou" for c in casos),
            f"{sum(c['tempo'] for c in casos):.2f}",
            "" if cobertura is None else f"{cobertura:.1f}", pasta.name,
        ])

    print(saida.strip().splitlines()[-1] if saida.strip() else "")
    print(f"Resumo salvo em: {pasta / 'resumo.md'}")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
