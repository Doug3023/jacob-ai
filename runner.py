from __future__ import annotations

from typing import Any

from .agent import carregar_contexto_lead, registrar_interacao, registrar_lead, root_agent


def preparar_payload(
    lead_id: str,
    mensagem: str,
    *,
    nome: str | None = None,
    telefone: str | None = None,
    historico_limite: int = 20,
    max_contexto_chars: int = 4000,
) -> dict[str, Any]:
    """
    Prepara o payload com contexto para uso no pipeline do agente.
    Nao chama o modelo diretamente; isso fica para o integrador (ex.: WhatsApp).
    """
    if nome or telefone:
        registrar_lead(lead_id, nome=nome, telefone=telefone)

    registrar_interacao(lead_id, "user", mensagem)

    historico_limite = max(1, min(historico_limite, 50))
    contexto = carregar_contexto_lead(lead_id, limit=historico_limite)
    if max_contexto_chars and len(contexto) > max_contexto_chars:
        contexto = contexto[:max_contexto_chars]
    instruction = f"{contexto}\n\n{root_agent.instruction}"

    return {
        "lead_id": lead_id,
        "mensagem": mensagem,
        "instruction": instruction,
    }


def registrar_resposta(lead_id: str, resposta: str) -> None:
    registrar_interacao(lead_id, "assistant", resposta)


if __name__ == "__main__":
    # Exemplo simples de uso local
    payload = preparar_payload(
        "5511999999999",
        "Oi, tenho interesse",
        nome="Ana",
        telefone="5511999999999",
    )
    print(payload["instruction"])
