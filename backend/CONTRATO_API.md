# Contrato da API e da classificação

## Execução local

No PowerShell, a partir da pasta `backend`:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs.
Os dados são armazenados em memória e desaparecem ao reiniciar, inclusive
quando o reload recarrega os arquivos. Use apenas um processo do servidor.
Esta implementação é destinada ao desenvolvimento local.

## Registro e consulta

`POST /relatos` recebe:

```json
{
  "texto": "Há um poste apagado na rua há três dias.",
  "localizacao": {"latitude": -20.3155, "longitude": -40.3128}
}
```

Retorna HTTP 201 com `id` (UUID), `texto`, `localizacao`, `status` (`Recebido`),
`criado_em` (data e hora UTC em ISO 8601) e `classificacao` (`null`).
O texto é limitado a 10–5000 caracteres após remoção dos espaços das extremidades.
Latitude: -90 a 90. Longitude: -180 a 180. Campos adicionais são rejeitados.

`GET /relatos` retorna `{"relatos": [...]}`, em ordem de cadastro.
`GET /relatos/{id}` retorna um relato individual.

## Integração com a Frente 3

O backend não chama o Groq automaticamente. A Frente 3 deve obter o texto,
classificá-lo e enviar o resultado para `PUT /relatos/{id}/classificacao`:

```json
{
  "categoria": "Iluminação",
  "prioridade": "Média",
  "setor": "Iluminação Pública",
  "risco_associado": "Baixa visibilidade durante a noite.",
  "informacoes_relevantes": ["Poste apagado", "Problema há três dias"]
}
```

Categorias: Infraestrutura, Iluminação, Limpeza Urbana, Trânsito, Segurança,
Meio Ambiente. Prioridades: Alta, Média, Baixa. Os valores devem corresponder
exatamente, incluindo acentos. A prioridade do exemplo é ilustrativa;
as regras de priorização pertencem à Frente 3.

`setor`: 1–150 caracteres. `risco_associado`: 1–1000 caracteres.
`informacoes_relevantes`: opcional, no máximo 20 textos; padrão `[]`.
Todos os demais campos da classificação são obrigatórios.

A rota retorna HTTP 200 com o relato atualizado e muda `Recebido` para
`Classificado`. Reenviar substitui a classificação anterior. Não há rota
de atualização dos demais status nesta entrega.
O contrato está proposto para alinhamento com a Frente 3.

## Erros e frontend

HTTP 422: dados inválidos ou identificador fora do formato UUID.
HTTP 404: relato não encontrado (`{"detail": "Relato não encontrado"}`).
Uma classificação inválida não altera o relato existente.

CORS permite `http://localhost:5173` e `http://127.0.0.1:5173`.
Para outra origem, defina `CORS_ORIGINS` com URLs separadas por vírgulas
antes de iniciar o servidor. Esta rota de classificação não tem autenticação;
o controle de acesso deve ser definido antes de disponibilizá-la publicamente.

## Testes

A partir da raiz do projeto:

```powershell
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\backend\venv\Scripts\python.exe -B -m pytest -q
```

Os testes não precisam de banco nem de chave do Groq.
