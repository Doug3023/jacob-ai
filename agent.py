import json
import os

import google.generativeai as genai

from firebase_client import montar_contexto, salvar_conversa, salvar_lead


# Configura API do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ==============================
# Carregar configuração produto
# ==============================
def carregar_produto():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_json = os.path.join(base_dir, "product_config.json")

    with open(caminho_json, "r", encoding="utf-8-sig") as f:
        return json.load(f)


produto = carregar_produto()


# ==============================
# Criar modelo Gemini
# ==============================
model = genai.GenerativeModel("gemini-2.0-flash")


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
- Quebrar objeções comuns (preço, confiança, eficácia, prazo).
- Reforçar valor percebido.
- Conduzir naturalmente para a decisão de compra.

Estilo de comunicação:
- Profissional
- Seguro
- Simples
- Persuasivo sem pressão

Estratégia:
- Se o usuário perguntar preço, explique o valor e o porquê.
- Se o usuário demonstrar dúvida, esclareça com objetividade.
- Se o usuário demonstrar interesse, avance para o fechamento.
- Sempre mantenha o foco no {produto['produto']}.

Regra absoluta:
- Use SOMENTE as informações fornecidas acima.
- Seu objetivo é fechar a venda com ética e clareza.
"""


# ==============================
# Função principal do agente
# ==============================
def root_agent(mensagem_usuario: str, contexto: str = "") -> str:
    prompt = f"""
{SYSTEM_PROMPT}

Histórico recente da conversa:
{contexto}

Mensagem do usuário:
{mensagem_usuario}

Resposta do Jacob:
"""

    resposta = model.generate_content(prompt)

    return resposta.text


# ==============================
# Firebase helpers
# ==============================
def registrar_lead(lead_id: str, **dados) -> None:
    salvar_lead(lead_id, dados)


def registrar_interacao(lead_id: str, role: str, mensagem: str) -> None:
    salvar_conversa(lead_id, role, mensagem)


def carregar_contexto_lead(lead_id: str, limit: int = 20) -> str:
    return montar_contexto(lead_id, limit=limit)
