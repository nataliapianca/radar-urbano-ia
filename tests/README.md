# Testes (Frente 4)

Testes automatizados do Radar Urbano IA com **pytest**. Nenhum teste chama
serviços externos: o Groq e o Geoapify são substituídos por dublês, então a
suíte roda **sem internet, sem banco e sem chaves de API**.

## Como rodar

A partir da raiz do repositório, com o ambiente virtual do backend ativo:

```bash
pip install -r backend/requirements-dev.txt

python -B -m pytest -q                 # rodada rápida
python -B -m pytest -v                 # mostra o nome de cada teste
python -B -m pytest -q --cov           # com cobertura de código
python tests/registrar_resultados.py   # roda tudo e salva o registro (ver abaixo)
```

## O que é testado

| Arquivo | Tipo | O que verifica |
|---|---|---|
| `test_api.py` | Integração | Fluxo básico: cadastro, consulta, classificação, isolamento entre instâncias, CORS |
| `test_relatos_cadastro.py` | Integração | Validação do `POST /relatos`: limites de 10–5000 caracteres (após `strip`), tipos, coordenadas nos limites e fora deles, `NaN`/`Infinity`, endereço/atribuição, campos extras e campos controlados pelo servidor (`id`, `status`, `classificacao`) |
| `test_relatos_consulta.py` | Integração | `GET /relatos` (ordem de cadastro), `GET /relatos/{id}` (404, 422), `PUT /relatos/{id}/classificacao`: todas as categorias e prioridades do contrato, acentos/caixa, limites de `setor`, `risco_associado` e `informacoes_relevantes`, reclassificação, e que uma classificação inválida **não altera** o relato |
| `test_localizacoes.py` | Unidade + integração | `POST /localizacoes/buscar`: 503 sem chave, validação da entrada, normalização e descarte de resultados inválidos, falhas de rede → 503 |
| `test_repositorio.py` | Unidade | Repositório em memória: IDs únicos, cópias defensivas, transição de status, cadastro concorrente |
| `test_urbania.py` | Unidade | `ia/UrbanIA.py`: modo mock, parâmetros enviados ao modelo (modelo, `temperature=0`, schema estrito), enums iguais aos do backend, resposta fora do contrato → `ErroIA`, erros do Groq → mensagens em português |
| `test_integracao_ia_backend.py` | Integração | `ia/integrar_backend.py` falando com a API real (em memória): classifica pendentes, ignora já classificados, `--relato-id`, falha da IA não interrompe os demais, classificação rejeitada (422) não altera o relato |
| `test_eval.py` | Unidade | Harness de eval: dataset válido, métricas com valores conhecidos, relatório/CSV/JSON/histórico, modo arquivo e linha de comando |

`conftest.py` concentra as fixtures (`client`, `relato_valido`,
`classificacao_valida`, `criar_relato`) e força `USE_MOCK=true` antes de
importar o módulo de IA.

## Registro dos resultados (para o vídeo)

```bash
python tests/registrar_resultados.py
```

Cria `tests/resultados/<data>/` com:

| Arquivo | Conteúdo |
|---|---|
| `resumo.md` | Situação geral, total/passou/falhou, cobertura e tabela por arquivo de teste |
| `junit.xml` | Relatório JUnit padrão |
| `saida.txt` | Saída completa do pytest, incluindo a tabela de cobertura |

e acrescenta uma linha em `tests/resultados/historico.csv`. Argumentos extras
são repassados ao pytest, por exemplo `python tests/registrar_resultados.py -k cadastro`.

A avaliação da IA (acurácia de categoria/prioridade) fica em [`eval/`](../eval/README.md).
