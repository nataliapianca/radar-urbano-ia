"""Testes unitários do repositório em memória (sem passar pela API)."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.repositorio import RepositorioRelatos
from app.schemas.classificacao import ClassificacaoIA
from app.schemas.relatos import Localizacao, RelatoCriar, StatusRelato


def _relato(texto="Buraco grande na avenida principal"):
    return RelatoCriar(texto=texto, localizacao=Localizacao(latitude=-20.3, longitude=-40.3))


def _classificacao():
    return ClassificacaoIA(categoria="Infraestrutura", prioridade="Alta",
                           setor="Obras Viárias", risco_associado="Risco de acidente")


def test_criar_define_id_status_e_data():
    repo = RepositorioRelatos()
    relato = repo.criar(_relato())
    assert relato.status == StatusRelato.RECEBIDO
    assert relato.classificacao is None
    assert relato.criado_em.tzinfo is not None


def test_ids_sao_unicos():
    repo = RepositorioRelatos()
    ids = {repo.criar(_relato()).id for _ in range(50)}
    assert len(ids) == 50


def test_buscar_inexistente_devolve_none():
    assert RepositorioRelatos().buscar(uuid4()) is None
    assert RepositorioRelatos().classificar(uuid4(), _classificacao()) is None


def test_copias_protegem_o_estado_interno():
    """Alterar o objeto devolvido não pode alterar o que está guardado."""
    repo = RepositorioRelatos()
    relato = repo.criar(_relato())
    relato.texto = "alterado por fora"
    relato.localizacao.latitude = 0
    repo.listar()[0].texto = "alterado pela lista"

    guardado = repo.buscar(relato.id)
    assert guardado.texto == "Buraco grande na avenida principal"
    assert guardado.localizacao.latitude == -20.3


def test_classificar_muda_status_somente_de_recebido():
    repo = RepositorioRelatos()
    relato = repo.criar(_relato())
    assert repo.classificar(relato.id, _classificacao()).status == StatusRelato.CLASSIFICADO

    # Um relato já "Em andamento" não volta para "Classificado" ao ser reclassificado
    repo._relatos[relato.id].status = StatusRelato.EM_ANDAMENTO
    assert repo.classificar(relato.id, _classificacao()).status == StatusRelato.EM_ANDAMENTO


def test_cadastro_concorrente_nao_perde_relatos():
    repo = RepositorioRelatos()
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda i: repo.criar(_relato(f"Relato concorrente {i:03d}")), range(200)))
    assert len(repo.listar()) == 200
