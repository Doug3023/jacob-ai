import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

# 1. PRIMEIRO: Criamos o app (Obrigatório ser antes das rotas)
app = FastAPI()

# 2. SEGUNDO: Configuramos o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. TERCEIRO: Conectamos ao Firebase
firebase_config = os.getenv("FIREBASE_SERVICE_ACCOUNT")
if firebase_config:
    try:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase conectado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar Firebase: {e}")
        db = None
else:
    db = None
    print("Variável FIREBASE_JSON não encontrada!")

# 4. QUARTO: Importamos o Agente (Só agora que o DB já existe)
# Certifique-se que o arquivo agent.py está na mesma pasta
try:
    from agent import root_agent, carregar_contexto_lead, registrar_interacao
except Exception as e:
    print(f"Erro ao importar agent.py: {e}")

# --- AGORA SIM, AS ROTAS (Todas abaixo do app = FastAPI) ---

@app.post("/chat")
async def chat(dados: dict):
    try:
        lead_id = dados.get("lead_id", "5511999999999")
        mensagem = dados.get("mensagem")
        contexto = carregar_contexto_lead(lead_id)
        resposta = root_agent(mensagem, contexto)
        registrar_interacao(lead_id, "user", mensagem)
        registrar_interacao(lead_id, "model", resposta)
        return {"lead_id": lead_id, "resposta": resposta}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/stats")
def get_stats():
    try:
        if not db: return {"erro": "Firebase desconectado"}
        leads_ref = db.collection("leads").get()
        return {"conversas": len(leads_ref), "cliques": 0, "vendas": 0, "receita": "R$ 0,00"}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/listar-conversas")
def listar_conversas():
    try:
        if not db: return []
        leads_ref = db.collection("leads").stream()
        return [{"id": d.id, "nome": d.to_dict().get("nome", "Novo"), "telefone": d.id} for d in leads_ref]
    except:
        return []

@app.get("/configuracao-produto")
def get_config():
    try:
        doc = db.collection("configuracoes").document("jacob_config").get()
        return doc.to_dict() if doc.exists else {}
    except:
        return {}

@app.post("/configuracao-produto")
def save_config(dados: dict):
    try:
        db.collection("configuracoes").document("jacob_config").set(dados)
        return {"status": "sucesso"}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/")
def home():
    return {"status": "Jacob API Rodando com Sucesso!"}