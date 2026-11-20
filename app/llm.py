"""Comunicação com o modelo de IA: chamada, leitura do JSON, validação e tentativas."""
import json
import logging
import re

from openai import OpenAI
from pydantic import ValidationError

from app import config
from app.prompt import SYSTEM_PROMPT, montar_mensagem_usuario
from app.schemas import ClassificacaoIA

log = logging.getLogger("classificador")

_cliente: OpenAI | None = None

def _get_cliente() -> OpenAI:
    # Cria o cliente uma vez só e reaproveita
    global _cliente
    if _cliente is None:
        if not config.LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY não definida no .env")
        # max_retries=0: quem controla as novas tentativas é a nossa função classificar()
        _cliente = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL, timeout=20, max_retries=0)
    return _cliente

def extrair_json(texto: str) -> dict:
    # Alguns modelos devolvem ```json ... ```; pega só o que está entre { e }
    texto = re.sub(r"```(?:json)?", "", texto).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError(f"Nenhum JSON encontrado na resposta: {texto[:200]}")
    return json.loads(texto[inicio : fim + 1])


def _chamar_modelo(mensagem: str) -> str:
    resposta = _get_cliente().chat.completions.create(
        model=config.LLM_MODEL,
        temperature=0,  # respostas mais estáveis para classificação
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": montar_mensagem_usuario(mensagem)},
        ],
    )
    return resposta.choices[0].message.content or ""


def classificar_mock(mensagem: str) -> ClassificacaoIA:
    # Classificador por palavras-chave, para testar sem chave de API
    t = mensagem.lower()
    if any(p in t for p in ["cobrad", "boleto", "reembolso", "estorno", "pagamento", "nota fiscal"]):
        setor = "financeiro"
    elif any(p in t for p in ["erro", "login", "senha", "não funciona", "nao funciona", "defeito", "acesso"]):
        setor = "suporte"
    elif any(p in t for p in ["orçamento", "orcamento", "preço", "preco", "plano", "comprar"]):
        setor = "comercial"
    else:
        setor = "atendimento"

    if any(p in t for p in ["obrigad", "parabéns", "parabens", "excelente", "adorei"]):
        categoria, sentimento = "elogio", "positivo"
    elif any(p in t for p in ["absurdo", "péssimo", "pessimo", "reclam", "problema", "erro", "cobrad"]):
        categoria, sentimento = "reclamacao", "negativo"
    elif "?" in t:
        categoria, sentimento = "duvida", "neutro"
    else:
        categoria, sentimento = "solicitacao", "neutro"

    prioridade = "alta" if any(p in t for p in ["urgente", "procon", "processar", "cancelar", "duas vezes"]) else "media"
    return ClassificacaoIA(
        categoria=categoria, setor=setor, prioridade=prioridade, sentimento=sentimento,
        resumo=mensagem[:120], confianca=0.7,
    )


def classificar(mensagem: str) -> tuple[ClassificacaoIA | None, str]:
    """Devolve (classificação, nome do modelo). Classificação None = IA falhou."""
    if config.LLM_PROVIDER == "mock":
        return classificar_mock(mensagem), "mock"

    for tentativa in range(1, config.MAX_TENTATIVAS + 1):
        try:
            bruto = _chamar_modelo(mensagem)
            return ClassificacaoIA(**extrair_json(bruto)), config.LLM_MODEL
        except (ValueError, ValidationError) as erro:
            # JSON quebrado ou valores fora das categorias: tenta de novo
            log.warning("Tentativa %d: resposta inválida da IA: %s", tentativa, erro)
        except Exception as erro:
            # Falha de rede, chave inválida, limite de uso etc.
            log.error("Tentativa %d: erro ao chamar a IA: %s", tentativa, erro)
    return None, config.LLM_MODEL
