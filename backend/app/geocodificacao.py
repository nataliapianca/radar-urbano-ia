"""Integração de geocodificação de endereço com o Geoapify."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GeocodificacaoIndisponivel(Exception):
    pass


def buscar_endereco(endereco: str) -> list[dict]:
    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    if not api_key:
        raise GeocodificacaoIndisponivel(
            "A busca de endereços ainda não foi configurada. Defina GEOAPIFY_API_KEY no backend."
        )

    parametros = urlencode({
        "text": endereco,
        "format": "json",
        "limit": 3,
        "lang": "pt",
        "filter": "countrycode:br",
        "apiKey": api_key,
    })
    requisicao = Request(
        f"https://api.geoapify.com/v1/geocode/search?{parametros}",
        headers={"Accept": "application/json", "User-Agent": "RadarUrbanoIA/1.0"},
    )

    try:
        with urlopen(requisicao, timeout=10) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as erro:
        raise GeocodificacaoIndisponivel(
            "Não foi possível consultar o serviço de endereços agora. Tente novamente."
        ) from erro

    resultados = []
    for item in dados.get("results", []):
        try:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
            descricao = item.get("formatted", "").strip()
            fonte = item.get("datasource", {}).get("attribution")
        except (KeyError, TypeError, ValueError):
            continue
        if descricao and -90 <= latitude <= 90 and -180 <= longitude <= 180:
            resultados.append({
                "latitude": latitude,
                "longitude": longitude,
                "endereco": descricao[:300],
                "atribuicao": fonte[:300] if fonte else None,
            })
    return resultados
