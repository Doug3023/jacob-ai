import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
from agent import root_agent, carregar_contexto_lead, registrar_interacao

@app.post("/chat")
async def chat(dados: dict):
    lead_id = dados.get("lead_id")
    mensagem = dados.get("mensagem")

    # 1. Busca o que eles já conversaram antes (Memória)
    contexto = carregar_contexto_lead(lead_id)

    # 2. Jacob gera a resposta usando os dados do seu Painel Firebase
    resposta = root_agent(mensagem, contexto)

    # 3. Salva a interação para ele não esquecer na próxima
    registrar_interacao(lead_id, "user", mensagem)
    registrar_interacao(lead_id, "model", resposta)

    return {"lead_id": lead_id, "resposta": resposta}

app = FastAPI()

# Configuração de CORS para o Dashboard acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectando ao Firebase usando a variável de ambiente do Render
firebase_config = os.getenv("FIREBASE_JSON")
if firebase_config:
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None
    print("Firebase não configurado!")

@app.get("/stats")
def get_stats():
    try:
        if not db:
            return {"erro": "Firebase não conectado"}
            
        # Conta quantos Leads totais você tem
        leads_ref = db.collection("leads").stream()
        total_leads = sum(1 for _ in leads_ref)

        return {
            "conversas": total_leads,
            "cliques": 0,
            "vendas": 0,
            "receita": "R$ 0,00"
        }
    except Exception as e:
        return {"erro": str(e)}

@app.get("/listar-conversas")
def listar_conversas():
    try:
        if not db:
            return {"erro": "Firebase não conectado"}

        # Puxa os leads do seu Firebase
        leads_ref = db.collection("leads").stream()
        lista = []
        for doc in leads_ref:
            dados = doc.to_dict()
            lista.append({
                "id": doc.id,
                "nome": dados.get("nome", "Usuário Novo"),
                "telefone": dados.get("telefone", doc.id),
                "tempo": "Ativo agora"
            })
        return lista
    except Exception as e:
        return {"erro": str(e)}
@app.get("/configuracao-produto")
def get_config():
    doc = db.collection("configuracoes").document("jacob_config").get()
    return doc.to_dict() if doc.exists else {}

@app.post("/configuracao-produto")
def save_config(dados: dict):
    db.collection("configuracoes").document("jacob_config").set(dados)
    return {"status": "sucesso"}

@app.get("/")
def home():
    return {"status": "Jacob API Rodando!"}
