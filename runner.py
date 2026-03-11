from agent import (
    root_agent,
    registrar_interacao,
    registrar_lead,
    carregar_contexto_lead
)


def preparar_payload(lead_id, mensagem, nome=None, telefone=None):

    if nome or telefone:
        registrar_lead(lead_id, nome=nome, telefone=telefone)

    contexto = carregar_contexto_lead(lead_id)

    resposta = root_agent(mensagem, contexto)

    registrar_interacao(lead_id, "user", mensagem)
    registrar_interacao(lead_id, "assistant", resposta)

    return {
        "lead_id": lead_id,
        "resposta": resposta
    }


# teste simples
if __name__ == "__main__":

    payload = preparar_payload(
        "5511999999999",
        "quanto custa?",
        nome="Teste",
        telefone="5511999999999"
    )

    print(payload)