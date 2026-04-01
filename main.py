import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Configuração do App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Conexão Firebase (Melhorada)
db = None
firebase_config = os.getenv("FIREBASE_SERVICE_ACCOUNT")

if firebase_config:
    try:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase conectado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar Firebase: {e}")
else:
    print("⚠️ Variável FIREBASE_SERVICE_ACCOUNT não encontrada!")

# 3. Importação Direta (Se o agent.py estiver errado, o servidor vai avisar no Log)
# Removi o try/except daqui para você ver o erro real nos logs do Render
from agent import root_agent, carregar_contexto_lead, registrar_interacao

# --- ROTAS ---

@app.post("/chat")
async def chat(dados: dict):
    try:
        if not db:
            return {"erro": "Banco de dados offline"}

        lead_id = dados.get("lead_id", "teste_padrao")
        mensagem = dados.get("mensagem")
        
        if not mensagem:
            return {"erro": "Mensagem vazia"}

        # Busca a configuração do produto no Firebase
        doc = db.collection("configuracoes").document("jacob_config").get()
        config_produto = doc.to_dict() if doc.exists else {}
        
        # Pega o histórico do lead
        contexto = carregar_contexto_lead(lead_id)
        
        # CHAMA O AGENTE (Certifique-se que o agent.py aceita config_produto!)
        resposta = root_agent(mensagem, contexto, config_produto) 
        
        # Salva a conversa
        registrar_interacao(lead_id, "user", mensagem)
        registrar_interacao(lead_id, "model", resposta)
        
        return {"lead_id": lead_id, "resposta": resposta}
    except Exception as e:
        print(f"Erro na rota /chat: {e}")
        return {"erro": str(e)}

@app.get("/configuracao-produto")
def get_config():
    try:
        doc = db.collection("configuracoes").document("jacob_config").get()
        return doc.to_dict() if doc.exists else {"aviso": "Nenhuma config encontrada"}
    except Exception as e:
        return {"erro": str(e)}

@app.post("/configuracao-produto")
def save_config(dados: dict):
    try:
        db.collection("configuracoes").document("jacob_config").set(dados)
        return {"status": "sucesso"}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/")
def home():
    return {"status": "Jacob API Online"}
