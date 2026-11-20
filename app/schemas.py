"""Modelos de entrada e saída da API (validação com Pydantic)."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Categoria(str, Enum):
    duvida = "duvida"
    reclamacao = "reclamacao"
    solicitacao = "solicitacao"
    elogio = "elogio"
    outro = "outro"


class Setor(str, Enum):
    suporte = "suporte"
    financeiro = "financeiro"
    comercial = "comercial"
    atendimento = "atendimento"


class Prioridade(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class Sentimento(str, Enum):
    positivo = "positivo"
    neutro = "neutro"
    negativo = "negativo"


# O que o cliente envia para a API
class MensagemEntrada(BaseModel):
    mensagem: str = Field(..., min_length=3, max_length=4000, description="Texto escrito pelo cliente")
    remetente: str | None = Field(None, max_length=200, description="Nome ou e-mail do cliente (opcional)")


# O que a IA precisa devolver (se vier diferente, a resposta é rejeitada)
class ClassificacaoIA(BaseModel):
    categoria: Categoria
    setor: Setor
    prioridade: Prioridade
    sentimento: Sentimento
    resumo: str = Field(..., min_length=3, max_length=300)
    confianca: float = Field(..., ge=0, le=1)


# Resposta final da API (classificação + dados de controle)
class ClassificacaoSaida(ClassificacaoIA):
    id: str
    remetente: str | None
    mensagem_original: str
    precisa_revisao: bool
    modelo: str
    recebido_em: datetime
