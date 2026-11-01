# Eval — avaliação da classificação da IA (Frente 4)

O harness roda um conjunto de relatos com **categoria e prioridade esperadas**
pela IA (`ia/UrbanIA.py`), compara com o que a IA devolveu e gera métricas de
acerto/erro e um relatório para a apresentação.

```
eval/
├── dataset/relatos_eval.json   → gabarito: 40 relatos rotulados
├── metricas.py                 → cálculo das métricas (Python puro)
├── rodar_eval.py               → executa a avaliação e salva os resultados
└── resultados/                 → uma pasta por execução + historico.csv
```

## Como rodar

A partir da raiz do repositório, com as dependências de `backend/requirements-dev.txt`
instaladas e `GROQ_API_KEY` definida em `ia/.env`:

```bash
# Avaliação real (chama o Groq uma vez por relato)
python eval/rodar_eval.py --modo groq --rotulo "prompt v1"

# Se o plano gratuito do Groq limitar as chamadas, espere entre elas
python eval/rodar_eval.py --modo groq --pausa 2

# Só alguns casos
python eval/rodar_eval.py --modo groq --ids IL01,IN01,TR01

# Recalcular as métricas de uma execução anterior, sem chamar o Groq
python eval/rodar_eval.py --modo arquivo --entrada eval/resultados/<pasta>/resultado.json

# Testar o próprio harness, sem chave (resposta fixa — métricas sem valor real)
python eval/rodar_eval.py --modo mock
```

Outras opções: `--limite N`, `--dataset outro.json`, `--sem-contrato`,
`--min-acuracia 0.8` (sai com código 1 se a acurácia de categoria ou de
prioridade ficar abaixo do valor; útil para CI).

## Dataset

`dataset/relatos_eval.json` tem 40 relatos ambientados na Grande Vitória:
6 por categoria (2 de cada prioridade) e 4 relatos em linguagem informal
(sem acento, gírias, sem informar o tempo).

| Campo | Descrição |
|---|---|
| `id` | Identificador (`IL` Iluminação, `IN` Infraestrutura, `TR` Trânsito, `LI` Limpeza Urbana, `SE` Segurança, `MA` Meio Ambiente, `EX` informais) |
| `texto` | O relato, como o cidadão escreveria |
| `categoria_esperada` / `prioridade_esperada` | Gabarito, com os valores exatos do contrato da API |
| `dificuldade` | `clara` ou `ambígua` (admite mais de uma leitura razoável) |
| `observacao` | Por que o gabarito é esse / qual seria a outra leitura |

A prioridade esperada segue as regras da Frente 3 (`ia/README.md`):
**Alta** = risco imediato à vida ou à integridade física; **Média** = atrapalha
ou pode causar dano se não for resolvido logo; **Baixa** = incômodo sem risco
imediato. O gabarito foi definido pela equipe e deve ser revisado em grupo —
ao mudar um rótulo, rode o modo `arquivo` para recalcular sem gastar cota.

## Métricas

| Métrica | O que significa |
|---|---|
| **Acurácia de categoria / prioridade** | % de relatos em que a IA acertou o campo |
| **Acerto de categoria e prioridade** | % de relatos em que a IA acertou os dois ao mesmo tempo |
| **Precisão por classe** | Dos relatos que a IA marcou como X, quantos eram X |
| **Revocação por classe** | Dos relatos que eram X, quantos a IA marcou como X |
| **F1 / F1 macro** | Média harmônica de precisão e revocação; o macro é a média entre as classes (não favorece classes com mais casos) |
| **Matriz de confusão** | Linha = esperado, coluna = previsto; mostra *com o que* a IA confunde cada classe |
| **Revocação de Alta** | Dos relatos que eram Alta, quantos a IA marcou como Alta — a métrica mais importante para segurança |
| **Subestimadas / superestimadas** | Erros de prioridade para menos (mais perigosos) e para mais |
| **Erros críticos** | Relato Alta classificado como Baixa |
| **Conformidade com o contrato** | % de respostas que o backend aceitou em `PUT /relatos/{id}/classificacao` (a resposta é enviada a uma instância da API em memória) |
| **Falhas da IA** | Chamadas que terminaram em `ErroIA` (chave, limite, timeout, JSON ou formato inválido); contam como erro nas acurácias |
| **Latência média / p95** | Tempo de resposta por relato |

As métricas também são separadas por dificuldade (`clara` × `ambígua`).

## Resultados

Cada execução cria `eval/resultados/<data>_<modo>/` com:

| Arquivo | Conteúdo |
|---|---|
| `relatorio.md` | Resumo, métricas por classe, matrizes de confusão e tabela de casos divergentes — pronto para mostrar no vídeo |
| `casos.csv` | Esperado × previsto de cada relato (separador `;`, abre direto no Excel) |
| `resultado.json` | Tudo, incluindo a resposta completa da IA; serve de entrada para o modo `arquivo` |

e acrescenta uma linha em `eval/resultados/historico.csv`, que permite
comparar execuções (por exemplo, antes e depois de mudar o prompt) usando o `--rotulo`.

> Execuções em modo `mock` devolvem sempre "Iluminação / Média" e servem apenas
> para validar o harness; o relatório traz um aviso. Use o modo `groq` para os
> números da apresentação.
