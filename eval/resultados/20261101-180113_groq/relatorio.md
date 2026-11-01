# Relatório de avaliação da IA — Radar Urbano IA

- **Data:** 2026-11-01T17:58:05
- **Modo:** groq
- **Modelo:** openai/gpt-oss-120b
- **Dataset:** `eval/dataset/relatos_eval.json` (versão 1.0, 40 relatos)

## Resumo

| Métrica | Resultado |
|---|---:|
| Acurácia de categoria | 80.0% (32/40) |
| Acurácia de prioridade | 77.5% (31/40) |
| Acerto de categoria **e** prioridade | 60.0% (24/40) |
| F1 macro — categoria | 79.3% |
| F1 macro — prioridade | 77.4% |
| Revocação de prioridade Alta | 84.6% (11/13) |
| Erros críticos (Alta classificada como Baixa) | 0 |
| Respostas aceitas pelo backend (contrato) | 100.0% |
| Falhas da IA (erro/timeout/formato) | 0 (0.0%) |
| Latência média / p95 | 4.70s / 7.49s |

## Por dificuldade do caso

| Dificuldade | Casos | Acurácia categoria | Acurácia prioridade |
|---|---:|---:|---:|
| ambígua | 13 | 61.5% | 76.9% |
| clara | 27 | 88.9% | 77.8% |

## Categoria

### Métricas por classe

| Classe | Precisão | Revocação | F1 | Casos |
|---|---:|---:|---:|---:|
| Infraestrutura | 77.8% | 100.0% | 87.5% | 7 |
| Iluminação | 85.7% | 85.7% | 85.7% | 7 |
| Limpeza Urbana | 100.0% | 57.1% | 72.7% | 7 |
| Trânsito | 85.7% | 85.7% | 85.7% | 7 |
| Segurança | 62.5% | 83.3% | 71.4% | 6 |
| Meio Ambiente | 80.0% | 66.7% | 72.7% | 6 |

### Matriz de confusão

| Esperado \ Previsto | Infraestrutura | Iluminação | Limpeza Urbana | Trânsito | Segurança | Meio Ambiente |
|---|---:|---:|---:|---:|---:|---:|
| Infraestrutura | **7** | 0 | 0 | 0 | 0 | 0 |
| Iluminação | 1 | **6** | 0 | 0 | 0 | 0 |
| Limpeza Urbana | 0 | 0 | **4** | 1 | 1 | 1 |
| Trânsito | 1 | 0 | 0 | **6** | 0 | 0 |
| Segurança | 0 | 1 | 0 | 0 | **5** | 0 |
| Meio Ambiente | 0 | 0 | 0 | 0 | 2 | **4** |

## Prioridade

### Métricas por classe

| Classe | Precisão | Revocação | F1 | Casos |
|---|---:|---:|---:|---:|
| Alta | 91.7% | 84.6% | 88.0% | 13 |
| Média | 61.9% | 92.9% | 74.3% | 14 |
| Baixa | 100.0% | 53.8% | 70.0% | 13 |

### Matriz de confusão

| Esperado \ Previsto | Alta | Média | Baixa |
|---|---:|---:|---:|
| Alta | **11** | 2 | 0 |
| Média | 1 | **13** | 0 |
| Baixa | 0 | 6 | **7** |

### Direção dos erros de prioridade

- Subestimadas (IA deu prioridade menor que a esperada): **2**
- Superestimadas (IA deu prioridade maior que a esperada): **7**
- Distância média entre níveis (0 = perfeito, 2 = pior): **0.23**

## Casos divergentes

| ID | Relato | Categoria (esperada → IA) | Prioridade (esperada → IA) | Obs. |
|---|---|---|---|---|
| IL01 | Fio de poste caído e soltando faísca na calçada da Rua Sete de Setembro, no Centro de V... | Iluminação → Infraestrutura ❌ | Alta → Alta | ambígua |
| IL06 | A luminária da quadra do bairro fica piscando de vez em quando à noite, na Rua das Palm... | Iluminação → Iluminação | Baixa → Média ❌ |  |
| IN05 | Pequenas rachaduras no asfalto da rua sem saída onde moro, Rua Ilha Rasa, Bairro de Fát... | Infraestrutura → Infraestrutura | Baixa → Média ❌ |  |
| IN06 | O banco da praça de Itapuã, em Vila Velha, está com uma ripa de madeira solta. Faz umas... | Infraestrutura → Infraestrutura | Baixa → Média ❌ |  |
| TR01 | O semáforo do cruzamento da Avenida Nossa Senhora da Penha com a Rua Ferreira Coelho es... | Trânsito → Trânsito | Alta → Média ❌ | ambígua |
| TR02 | Carro quebrado parado sem nenhuma sinalização logo depois da curva da Terceira Ponte, s... | Trânsito → Trânsito | Alta → Média ❌ |  |
| TR04 | A placa de PARE do cruzamento da Rua Anísio Fernandes Coelho, em Jardim da Penha, foi d... | Trânsito → Trânsito | Média → Alta ❌ | ambígua |
| TR05 | A faixa de pedestre da Rua Constante Sodré, na Praia do Canto, está bem apagada. A pint... | Trânsito → Infraestrutura ❌ | Baixa → Média ❌ |  |
| TR06 | Carros estacionam em fila dupla na porta da padaria da Rua Hugo Musso todo fim de tarde... | Trânsito → Trânsito | Baixa → Média ❌ |  |
| LI01 | Lixo hospitalar com seringas e agulhas foi descartado em sacos rasgados na calçada da R... | Limpeza Urbana → Segurança ❌ | Alta → Alta |  |
| LI02 | Entulho e restos de obra jogados ocupando metade da pista da Rodovia do Sol, em Vila Ve... | Limpeza Urbana → Trânsito ❌ | Alta → Alta | ambígua |
| LI04 | Tem um ponto de descarte irregular de móveis velhos e sofás no terreno da esquina da Ru... | Limpeza Urbana → Meio Ambiente ❌ | Média → Média |  |
| SE03 | O ponto de ônibus da Avenida Leitão da Silva fica sem iluminação e muito deserto à noit... | Segurança → Iluminação ❌ | Média → Média | ambígua |
| SE06 | Imóvel abandonado na Rua Graciano Neves com a porta aberta. Os moradores temem que vire... | Segurança → Segurança | Baixa → Média ❌ | ambígua |
| MA01 | Árvore grande com o tronco rachado, inclinada sobre a rede elétrica e as casas na Rua A... | Meio Ambiente → Segurança ❌ | Alta → Alta | ambígua |
| MA06 | Um bar na Rua Joaquim Lírio coloca som muito alto até meia-noite todos os fins de seman... | Meio Ambiente → Segurança ❌ | Baixa → Baixa | ambígua |

---
Gerado por `eval/rodar_eval.py`. Detalhes de cada caso em `casos.csv` e `resultado.json`.
