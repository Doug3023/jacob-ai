import os
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_LOADED = False
_DB = None


def _load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    # Prefer Jacob/.env, but also allow project root .env
    load_dotenv(os.path.join(_BASE_DIR, ".env"))
    load_dotenv(os.path.join(_BASE_DIR, "..", ".env"))
    _ENV_LOADED = True


def _get_project_id() -> str | None:
    _load_env()
    return os.getenv("FIREBASE_PROJECT_ID")


def _get_credentials_path() -> str:
    _load_env()
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not path:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT nao definido. "
            "Aponte para o JSON da conta de servico."
        )
    if os.path.isabs(path):
        return path
    # Resolve relative path against project root (parent of Jacob/)
    return os.path.abspath(os.path.join(_BASE_DIR, "..", path))


def _init_app() -> None:
    if firebase_admin._apps:
        return

    cred = credentials.Certificate(_get_credentials_path())
    project_id = _get_project_id()

    if project_id:
        firebase_admin.initialize_app(cred, {"projectId": project_id})
    else:
        firebase_admin.initialize_app(cred)


def get_firestore():
    global _DB
    _init_app()
    if _DB is None:
        _DB = firestore.client()
    return _DB


def salvar_lead(lead_id: str, dados: dict) -> None:
    db = get_firestore()
    payload = dict(dados)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    db.collection("leads").document(lead_id).set(payload, merge=True)


def salvar_conversa(lead_id: str, role: str, mensagem: str) -> None:
    db = get_firestore()
    evento = {
        "role": role,
        "mensagem": mensagem,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.collection("leads").document(lead_id).collection("conversas").add(evento)


def obter_lead(lead_id: str) -> dict | None:
    db = get_firestore()
    doc = db.collection("leads").document(lead_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def listar_conversas(lead_id: str, limit: int = 20) -> list[dict]:
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
    # Remocao simples de quebras de linha e limite de tamanho
    texto = texto.replace("\n", " ").replace("\r", " ")
    return texto[:500]


def montar_contexto(lead_id: str, limit: int = 20) -> str:
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
