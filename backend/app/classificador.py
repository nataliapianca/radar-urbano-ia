"""Classificação automática dos relatos pela IA (pasta ia/), em segundo plano."""
import logging
import sys
from pathlib import Path
from uuid import UUID

from app.repositorio import RepositorioRelatos
from app.schemas.classificacao import ClassificacaoIA

PASTA_IA = Path(__file__).resolve().parents[2] / "ia"
log = logging.getLogger("uvicorn.error")


def classificar_em_segundo_plano(repositorio: RepositorioRelatos, relato_id: UUID, texto: str):
    """Chama a IA e grava a classificação. Em caso de falha o relato segue como Recebido."""
    try:
        if str(PASTA_IA) not in sys.path:
            sys.path.insert(0, str(PASTA_IA))
        from UrbanIA import classificar_relato

        dados = ClassificacaoIA(**classificar_relato(texto))
        repositorio.classificar(relato_id, dados)
    except Exception as erro:  # a IA nunca deve derrubar a API
        log.warning("Falha ao classificar o relato %s: %s", relato_id, erro)
