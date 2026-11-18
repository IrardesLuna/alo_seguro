"""API do Alô Seguro.

Rodar (dentro da pasta backend, com o ambiente ativado):
    uvicorn app.main:app --reload
Depois abra http://127.0.0.1:8000
"""
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import agente, config, gemini, servico

app = FastAPI(title="Alô Seguro API", version="1.0.0")

# Permite abrir o site pelo Live Server do VS Code (ou direto do arquivo) e chamar a API local.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(null|http://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PedidoAnalise(BaseModel):
    plataforma: str = Field(description="redes_sociais, email ou links (também aceita whatsapp, instagram, snapchat, discord)")
    texto: str = Field(description="Mensagem ou link recebido")


# Limite simples de pedidos por pessoa, para não estourar a cota gratuita da IA.
_pedidos_por_ip: dict[str, deque] = defaultdict(deque)


def _verificar_limite(ip: str) -> None:
    agora = time.monotonic()
    fila = _pedidos_por_ip[ip]
    while fila and agora - fila[0] > 60:
        fila.popleft()
    if len(fila) >= config.LIMITE_POR_MINUTO:
        raise HTTPException(429, "Muitas análises seguidas. Espere um minuto e tente de novo.")
    fila.append(agora)


@app.get("/api/saude")
def saude():
    return {"status": "ok", "ia_configurada": gemini.configurado(), "modelo": config.GEMINI_MODEL}


@app.get("/api/plataformas")
def plataformas():
    return [
        {"id": chave, "nome": nome, "total_golpes": len(agente.base_golpes(chave))}
        for chave, nome in agente.CANAIS.items()
    ]


@app.post("/api/analisar")
def analisar(pedido: PedidoAnalise, request: Request):
    plataforma = pedido.plataforma.strip().lower()
    texto = pedido.texto.strip()

    if plataforma not in agente.PLATAFORMAS:
        raise HTTPException(422, "Escolha um canal válido.")
    if len(texto) < config.TAMANHO_MINIMO_TEXTO:
        raise HTTPException(422, "Cole a mensagem ou o link que você recebeu.")
    if len(texto) > config.TAMANHO_MAXIMO_TEXTO:
        raise HTTPException(422, f"O texto é muito longo. Cole até {config.TAMANHO_MAXIMO_TEXTO} caracteres.")

    _verificar_limite(request.client.host if request.client else "desconhecido")
    return servico.analisar(plataforma, texto)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/proj1.html")


# O site (HTML, CSS e JS) é servido pela própria API: tudo no mesmo endereço.
app.mount("/", StaticFiles(directory=config.PASTA_FRONTEND, html=True), name="site")
