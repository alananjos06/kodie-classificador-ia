"""Configurações lidas das variáveis de ambiente (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()

# Endereço e modelo padrão de cada provedor (todos usam o formato compatível com OpenAI)
PROVEDORES = {
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-3.5-flash-lite"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
}

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

_url_padrao, _modelo_padrao = PROVEDORES.get(LLM_PROVIDER, ("", "mock"))
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or _url_padrao
LLM_MODEL = os.getenv("LLM_MODEL") or _modelo_padrao

# Abaixo deste valor de confiança a mensagem vai para revisão humana
LIMITE_CONFIANCA = float(os.getenv("LIMITE_CONFIANCA", "0.6"))
# Quantas vezes tentar de novo se a IA devolver JSON inválido
MAX_TENTATIVAS = int(os.getenv("MAX_TENTATIVAS", "2"))
