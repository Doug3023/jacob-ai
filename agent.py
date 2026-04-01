import json
import os
from google import genai
from firebase_client import montar_contexto, salvar_conversa, salvar_lead

# 1. Criar cliente Gemini
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# 2. Função de Backup (Caso o Firebase falhe)
def carregar_produto_json():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_json = os.path.join(base_dir, "product_config.json")
        with open(caminho_json, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except:
        return {"produto": "Produto", "preco": "0.00", "publico": "Geral", "beneficios": [], "objeções": {}}

# ==============================
# Função principal do agente (CORRIGIDA COM 3 ARGUMENTOS)
# ==============================
def root_agent(mensagem_usuario: str, contexto: str = "", config_produto: dict = None) -> str:
    
    # 3. LOGICA DE DECISÃO: Firebase (config_produto) OU JSON?
    # Se o config_produto veio do Firebase, usamos ele. Se não, usamos o JSON.
    info = config_produto if config_produto else carregar_produto_json()

    # Monta o Prompt com os dados REAIS e ATUALIZADOS
    beneficios_lista = info.get('beneficios', [])
    if isinstance(beneficios_lista, str): # Caso venha como texto do Firebase
        beneficios_str = beneficios_lista
    else:
        beneficios_str = "\n".join([f"- {b}" for b in beneficios_lista])

    objecao = info.get('objeções', info.get('objecoes', {}))

    SYSTEM_PROMPT = f"""
Você é Jacob, um agente de vendas digital especializado em fechamento de vendas.

Informações oficiais do produto (ATUALIZADAS):
Produto: {info.get('produto', info.get('nome', 'Produto'))}
Preço: {info.get('preco', 'Consulte-nos')}
Público: {info.get('publico', 'Interessados')}
Dor principal: {info.get('dor_principal', 'Não informada')}

Benefícios principais:
{beneficios_str}

Respostas para objeções:
Funciona? {objecao.get('funciona', 'Sim, com certeza.')}
Entrega? {objecao.get('entrega', 'Imediata.')}
Garantia? {objecao.get('garantia', '7 dias.')}

Regra absoluta: Use SOMENTE as informações acima para fechar a venda.
"""

    prompt = f"""
{SYSTEM_PROMPT}

Histórico recente:
{contexto}

Mensagem do usuário:
{mensagem_usuario}

Resposta do Jacob:
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text

# ==============================
# Firebase helpers (Mantidos)
# ==============================
def registrar_lead(lead_id: str, **dados) -> None:
    salvar_lead(lead_id, dados)

def registrar_interacao(lead_id: str, role: str, mensagem: str) -> None:
    salvar_conversa(lead_id, role, mensagem)

def carregar_contexto_lead(lead_id: str, limit: int = 20) -> str:
    return montar_contexto(lead_id, limit=limit)
