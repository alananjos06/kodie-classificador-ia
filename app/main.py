"""API FastAPI que recebe mensagens de clientes e devolve a classificação feita pela IA."""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI

from app import config
from app.llm import classificar
from app.schemas import ClassificacaoSaida, MensagemEntrada

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="Classificador de Mensagens com IA",
    description="Recebe a mensagem de um cliente e devolve categoria, setor, prioridade e resumo em JSON.",
    version="1.0.0",
)


@app.get("/health")
def health():
    # Usado para conferir se a API está no ar
    return {"status": "ok", "provedor": config.LLM_PROVIDER, "modelo": config.LLM_MODEL}


@app.post("/classificar", response_model=ClassificacaoSaida)
def classificar_mensagem(entrada: MensagemEntrada):
    resultado, modelo = classificar(entrada.mensagem)

    if resultado is None:
        # Se a IA falhar, a mensagem não se perde: vai para triagem manual
        dados = {
            "categoria": "outro", "setor": "atendimento", "prioridade": "media",
            "sentimento": "neutro", "resumo": "Não foi possível classificar automaticamente.",
            "confianca": 0.0,
        }
    else:
        dados = resultado.model_dump()

    return ClassificacaoSaida(
        **dados,
        id=str(uuid.uuid4()),
        remetente=entrada.remetente,
        mensagem_original=entrada.mensagem,
        precisa_revisao=dados["confianca"] < config.LIMITE_CONFIANCA,
        modelo=modelo,
        recebido_em=datetime.now(timezone.utc),
    )
