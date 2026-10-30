"""Classifica relatos pendentes da API usando UrbanIA e devolve o resultado."""

import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from UrbanIA import ErroIA, classificar_relato


def requisitar(api_url: str, caminho: str, metodo: str = "GET", dados=None):
    corpo = None if dados is None else json.dumps(dados, ensure_ascii=False).encode("utf-8")
    requisicao = Request(
        f"{api_url.rstrip('/')}{caminho}",
        data=corpo,
        method=metodo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(requisicao, timeout=15) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API respondeu HTTP {erro.code}: {detalhe}") from erro
    except (URLError, TimeoutError) as erro:
        raise RuntimeError(f"Não foi possível acessar a API em {api_url}: {erro}") from erro


def classificar_pendentes(api_url: str, relato_id: str | None = None) -> int:
    if relato_id:
        relatos = [requisitar(api_url, f"/relatos/{relato_id}")]
    else:
        relatos = requisitar(api_url, "/relatos")["relatos"]

    pendentes = [r for r in relatos if r["status"] == "Recebido"]
    if not pendentes:
        print("Nenhum relato pendente de classificação.")
        return 0

    falhas = 0
    for relato in pendentes:
        try:
            classificacao = classificar_relato(relato["texto"])
            atualizado = requisitar(
                api_url,
                f"/relatos/{relato['id']}/classificacao",
                metodo="PUT",
                dados=classificacao,
            )
            print(f"Relato {relato['id']} classificado: {atualizado['classificacao']['categoria']} / {atualizado['classificacao']['prioridade']}")
        except (ErroIA, RuntimeError, KeyError) as erro:
            falhas += 1
            print(f"Falha ao classificar relato {relato['id']}: {erro}")
    return falhas


def main():
    parser = argparse.ArgumentParser(description="Classifica relatos pendentes pela IA.")
    parser.add_argument("--api-url", default=os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--relato-id", help="Classifica apenas o relato informado")
    args = parser.parse_args()
    try:
        falhas = classificar_pendentes(args.api_url, args.relato_id)
    except (RuntimeError, KeyError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    raise SystemExit(1 if falhas else 0)


if __name__ == "__main__":
    main()
