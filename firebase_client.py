import os
import json
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore


_DB = None


def _init_app():
    """Inicializa Firebase apenas uma vez"""
    if firebase_admin._apps:
        return

    firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_json:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT nao definido nas variaveis de ambiente"
        )

    try:
        cred_dict = json.loads(firebase_json)
    except Exception as e:
        raise RuntimeError("Erro ao ler JSON do FIREBASE_SERVICE_ACCOUNT") from e

    cred = credentials.Certificate(cred_dict)

    project_id = os.environ.get("FIREBASE_PROJECT_ID")

    if project_id:
        firebase_admin.initialize_app(cred, {"projectId": project_id})
    else:
        firebase_admin.initialize_app(cred)


def get_firestore():
    """Retorna cliente Firestore"""
    global _DB

    _init_app()

    if _DB is None:
        _DB = firestore.client()

    return _DB


def salvar_lead(lead_id: str, dados: dict):
    db = get_firestore()

    payload = dict(dados)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    db.collection("leads").document(lead_id).set(payload, merge=True)


def salvar_conversa(lead_id: str, role: str, mensagem: str):
    db = get_firestore()

    evento = {
        "role": role,
        "mensagem": mensagem,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection("leads").document(lead_id).collection("conversas").add(evento)


def obter_lead(lead_id: str):
    db = get_firestore()

    doc = db.collection("leads").document(lead_id).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def listar_conversas(lead_id: str, limit: int = 20):
    db = get_firestore()

    refs = (
        db.collection("leads")
        .document(lead_id)
        .collection("conversas")
        .order_by("created_at", direction=firestore.Query.ASCENDING)
        .limit(limit)
        .stream()
    )

    return [r.to_dict() for r in refs]


def _sanitizar_texto(texto: str) -> str:
    texto = texto.replace("\n", " ").replace("\r", " ")
    return texto[:500]


def montar_contexto(lead_id: str, limit: int = 20):
    lead = obter_lead(lead_id)
    historico = listar_conversas(lead_id, limit=limit)

    partes = []

    if lead:
        nome = lead.get("nome") or "Nao informado"
        telefone = lead.get("telefone") or "Nao informado"

        partes.append(
            f"Lead: {_sanitizar_texto(str(nome))} | Telefone: {_sanitizar_texto(str(telefone))}"
        )
    else:
        partes.append("Lead: Nao encontrado")

    if historico:
        partes.append("Historico recente:")

        for h in historico:
            role = h.get("role", "user")
            msg = h.get("mensagem", "")

            partes.append(f"- {role}: {_sanitizar_texto(str(msg))}")

    else:
        partes.append("Historico recente: vazio")

    return "\n".join(partes)