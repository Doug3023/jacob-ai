import json
import os
from google import genai

from firebase_client import montar_contexto, salvar_conversa, salvar_lead


# ==============================
# Configurar cliente Gemini
# ==============================
API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não definida nas variáveis de ambiente")

client = genai.Client(api_key=API_KEY)


# ==============================
# Carregar configuração produto
# ==============================
def carregar_produto():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_json = os.path.join(base_dir, "product_config.json")

    if not os.path.exists(caminho_json):
        raise RuntimeError("Arquivo product_config.json não encontrado")

    with open(caminho_json, "r", encoding="utf-8") as f:
        return json.load(f)


produto = carregar_produto()


# ==============================
# Prompt principal do Jacob
# ==============================
SYSTEM_PROMPT = f"""
Você é Jacob, um agente de vendas digital especializado em fechamento de vendas.

Contexto obrigatório:
- O usuário clicou em um anúncio do produto {produto['produto']}.
- Ele já conhece o produto e tem interesse.
- Sua função NÃO é apresentar o produto do zero.
- Sua função é ajudar o usuário a tomar a decisão final de compra.

Informações oficiais do produto:
- Produto: {produto['produto']}
- Preço: {produto['preco']}
- Público: {produto['publico']}
- Dor principal: {produto['dor_principal']}

Benefícios principais:
{chr(10).join([f"- {b}" for b in produto['beneficios']])}

Respostas para objeções:
- Funciona? {produto['objeções']['funciona']}
- Entrega? {produto['objeções']['entrega']}
- Garantia? {produto['objeções']['garantia']}

Comportamento:
- Seja direto, claro e confiante.
- Não use linguagem genérica de atendimento.
- Não faça perguntas abertas demais.
- Não fale sobre outros produtos.
- Não invente benefícios ou promessas irreais.
- Não use tom exageradamente empolgado.

Objetivo principal:
- Reduzir dúvidas finais.
- Quebrar objeções comuns.
- Reforçar valor percebido.
- Conduzir para decisão de compra.

Estilo:
- Profissional
- Seguro
- Simples
- Persuasivo sem pressão

Regra absoluta:
- Use SOMENTE as informações fornecidas.
"""


# ==============================
# Função principal do agente
# ==============================
def root_agent(mensagem_usuario: str, contexto: str = "") -> str:

    prompt = f"""
{SYSTEM_PROMPT}

Histórico recente:
{contexto}

Mensagem do usuário:
{mensagem_usuario}

Resposta do Jacob:
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return "Não consegui gerar uma resposta no momento."

    except Exception as e:
        print("Erro Gemini:", e)
        return "Ocorreu um erro ao gerar a resposta."


# ==============================
# Firebase helpers
# ==============================
def registrar_lead(lead_id: str, **dados):
    salvar_lead(lead_id, dados)


def registrar_interacao(lead_id: str, role: str, mensagem: str):
    salvar_conversa(lead_id, role, mensagem)


def carregar_contexto_lead(lead_id: str, limit: int = 20):
    return montar_contexto(lead_id, limit=limit)