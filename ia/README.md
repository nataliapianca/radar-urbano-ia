# Inteligência Artificial (Frente 3)

Esta pasta contém a IA do Radar UrbanIA. Ela recebe o relato do cidadão, pede as informações que faltam e classifica o problema em **categoria**, **prioridade** e **setor**, no formato combinado com o Backend.

A IA usa o **Groq** pelo cliente `openai`, com o modelo `openai/gpt-oss-120b`.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `UrbanIA.py` | Lógica da IA: cliente Groq, prompts, schemas, validação, tratamento de erros e mock. Não tem `input`, `print` nem loop. |
| `Chat.py` | Interface no terminal para testar a IA: recebe o relato, faz até 3 perguntas de complemento e mostra a classificação. |
| `.env` | Variáveis de configuração (não vai para o Git). |

## Como rodar

1. Instale as dependências (de preferência dentro de um ambiente virtual):
   ```
   pip install openai python-dotenv pydantic
   ```
2. Crie o arquivo `ia/.env` (veja abaixo).
3. Dentro da pasta `ia/`, rode:
   ```
   python Chat.py
   ```
4. Escreva o relato, responda às perguntas da IA e veja o JSON da classificação. Digite `sair` para encerrar.

## Variáveis do `.env`

```
GROQ_API_KEY=sua_chave_aqui
USE_MOCK=false
```

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave da API do Groq. Gere em https://console.groq.com/keys. **Nunca coloque a chave no código.** |
| `USE_MOCK` | `false` (padrão): usa a IA real. `true`: devolve respostas fixas, sem chamar o Groq. |
No .env	Resposta à pergunta "usar o mock?"	Quem responde
USE_MOCK=false	A IA de verdade (Groq)
USE_MOCK=true	A resposta pronta (mock)


O `.env` está no `.gitignore` e não deve ser enviado ao repositório.

## Contrato com o Backend

O Backend não chama o Groq. A Frente 3 classifica o relato e envia o resultado para `PUT /relatos/{id}/classificacao`:

```json
{
  "categoria": "Iluminação",
  "prioridade": "Média",
  "setor": "Iluminação Pública",
  "risco_associado": "Baixa visibilidade durante a noite.",
  "informacoes_relevantes": ["Poste apagado", "Problema há três dias"]
}
```

| Campo | Regra |
|---|---|
| `categoria` | `Infraestrutura`, `Iluminação`, `Limpeza Urbana`, `Trânsito`, `Segurança` ou `Meio Ambiente` |
| `prioridade` | `Alta`, `Média` ou `Baixa` |
| `setor` | Texto livre, de 1 a 150 caracteres |
| `risco_associado` | Texto de 1 a 1000 caracteres |
| `informacoes_relevantes` | Opcional, lista com no máximo 20 textos (padrão `[]`) |

A rota retorna HTTP 200 e muda o status do relato de `Recebido` para `Classificado`. Reenviar substitui a classificação anterior.

A resposta é garantida em duas camadas:
1. **No Groq:** `response_format` com `json_schema` e `strict: True`, já com as listas permitidas do contrato.
2. **No nosso código:** validação com Pydantic (classe `Classificacao`), que confere as listas permitidas, os limites de tamanho e o máximo de 20 itens.

## Regras de prioridade

| Prioridade | Quando usar | Exemplos |
|---|---|---|
| **Alta** | Risco imediato à vida ou à integridade física | Fio caído, buraco grande em via movimentada, vazamento perigoso |
| **Média** | Atrapalha ou pode causar dano se não for resolvido logo | Poste apagado, semáforo com defeito |
| **Baixa** | Incômodo sem risco imediato | Mato alto, pichação, lixo pontual |

## Fluxo da IA

1. **Verificação** (`verificar_relato`): confere se o relato tem localização, tamanho/gravidade e há quanto tempo o problema existe. Se faltar algo, devolve uma pergunta. O chat faz no máximo 3 perguntas.
2. **Classificação** (`classificar_relato`): devolve o dicionário no formato do contrato.

Exemplo de uso direto no código:

```python
from UrbanIA import classificar_relato, ErroIA

try:
    resultado = classificar_relato("Buraco de 90 cm na rua Rio Muriaé, 19, há 3 dias.")
    print(resultado["categoria"], resultado["prioridade"], resultado["setor"])
except ErroIA as e:
    print(e)
```

## Tratamento de erros

Todas as chamadas ao Groq passam pela função `_chamar_groq`. O cliente tem `timeout=30` segundos e `max_retries=2`. Qualquer falha vira a exceção `ErroIA`, com uma mensagem em português:

| Erro original | Mensagem |
|---|---|
| `AuthenticationError` | Chave da API do Groq inválida ou ausente |
| `RateLimitError` | Limite de uso do Groq atingido |
| `APITimeoutError` | O Groq demorou demais para responder |
| `APIConnectionError` | Não foi possível conectar ao Groq |
| `APIError` | O Groq retornou um erro |
| `JSONDecodeError` | A IA devolveu uma resposta que não é um JSON válido |
| `ValidationError` (Pydantic) | Resposta fora do formato combinado com o Backend |

O `Chat.py` captura `ErroIA`, mostra a mensagem e continua rodando.

## Modo mock

Com `USE_MOCK=true` no `.env`:
- `verificar_relato` devolve `{"suficiente": true, "pergunta": ""}`;
- `classificar_relato` devolve o exemplo do contrato (poste apagado, Iluminação, Média);
- o Groq **não** é chamado, e a chave nem é necessária;
- o `Chat.py` mostra `[MODO] MOCK ATIVO` no início e junto de cada resposta (com `USE_MOCK=false`, mostra `[MODO] IA ATIVA`).

O mock serve **apenas para testes**. No uso normal, deixe `USE_MOCK=false`.
No .env	        /Resposta à pergunta "usar o mock?"    /Quem responde
USE_MOCK=false	             /Não	                   /A IA de verdade (Groq)
USE_MOCK=true	             /Sim	                   /A resposta pronta (mock)

## Bloqueios e alternativa de teste

**Situação atual:** a integração real com o Groq está funcionando. Teste feito com um relato de buraco de 90 cm, que retornou `Infraestrutura` / `Alta` / `Obras Viárias` no formato do contrato.

**Possíveis bloqueios:**
- Chave do Groq ausente, inválida ou expirada.
- Limite de uso do plano gratuito do Groq (rate limit).
- Instabilidade ou indisponibilidade do serviço do Groq.
- Falta de conexão com a internet.

**Alternativa de teste:** se algum desses bloqueios acontecer, ative `USE_MOCK=true` no `.env`. Assim, o restante do fluxo (Chat, integração com o Backend e testes automatizados) pode ser testado com uma resposta fixa no formato do contrato, sem depender do Groq.

## Observações

- A IA **não** gera telefones, e-mails ou sites de órgãos públicos, porque pode inventar dados. Se isso for necessário, os contatos virão de uma tabela fixa.
- O histórico do `Chat.py` fica apenas em memória por enquanto.
