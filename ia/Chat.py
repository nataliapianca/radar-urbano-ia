import json
from UrbanIA import classificar_relato, verificar_relato, ErroIA, USE_MOCK

MAX_PERGUNTAS = 3
historico = []

if USE_MOCK:
    MODO = "MOCK ATIVO (respostas fixas, o Groq não está sendo chamado)"
else:
    MODO = "IA ATIVA (classificação feita pelo Groq)"

print("Radar UrbanIA iniciado! Digite 'sair' para encerrar.")
print(f"[MODO] {MODO}")
print("Qual é a sua queixa?\n")

while True:
    pergunta = input("Você: ")

    if pergunta.lower() == "sair":
        print("Chat encerrado.")
        break

    relato = pergunta

    try:
        # Fase 1: coleta das informações que faltam
        for _ in range(MAX_PERGUNTAS):
            verificacao = verificar_relato(relato)

            if verificacao["suficiente"]:
                break

            print("Radar UrbanIA:", verificacao["pergunta"])
            complemento = input("Você: ")
            relato = relato + ". " + complemento

        # Fase 2: classificação
        classificacao = classificar_relato(relato)
    except ErroIA as e:
        print(f"\nRadar UrbanIA: Erro - {e}")
        print("Tente enviar a queixa novamente (ou digite 'sair').\n")
        continue

    historico.append({"relato": relato, "classificacao": classificacao})

    print(f"\nRadar UrbanIA: [{MODO}]")
    print(json.dumps(classificacao, ensure_ascii=False, indent=2))
    print("\nTem outra queixa? (ou digite 'sair')\n")
