"""API do Alô Seguro.

Rodar (dentro da pasta backend, com o ambiente ativado):
    uvicorn app.main:app --reload
Depois abra http://127.0.0.1:8000
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import agente, casos, config, conversa, gemini, servico, vazamentos

app = FastAPI(title="Alô Seguro API", version="1.0.0")

# Permite abrir o site pelo Live Server do VS Code (ou direto do arquivo) e chamar a API local.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(null|http://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


class PedidoConsulta(BaseModel):
    """Só o necessário para a consulta: nome, senha, cartão ou CPF nunca são pedidos."""
    email: str | None = Field(default=None, max_length=254, description="E-mail a verificar (opcional se houver telefone)")
    telefone: str | None = Field(default=None, max_length=30, description="Telefone com DDD (opcional se houver e-mail)")


class PedidoConversa(BaseModel):
    """O histórico vem do navegador a cada pergunta: o servidor não guarda a conversa."""
    historico: list[dict] = Field(max_length=20, description='Falas em ordem: {"papel": "usuario" ou "assistente", "texto": "..."}')
    contexto: dict | None = Field(default=None, description="Resumo opcional da análise de mensagem feita antes")


class CasoEntrada(BaseModel):
    plataforma: str
    texto: str = Field(max_length=4000)
    rotulo: str
    taticas: list[str] = []
    golpe_base: str | None = None
    licao: str = ""
    status: str = "pendente"
    reservado_para_teste: bool = False


class CasoEdicao(BaseModel):
    """Só os campos enviados são alterados."""
    plataforma: str | None = None
    texto: str | None = Field(default=None, max_length=4000)
    rotulo: str | None = None
    taticas: list[str] | None = None
    golpe_base: str | None = None
    licao: str | None = None
    status: str | None = None
    reservado_para_teste: bool | None = None


class PedidoSugestao(BaseModel):
    plataforma: str
    texto: str = Field(max_length=4000)


class PedidoAnalise(BaseModel):
    plataforma: str = Field(description="redes_sociais, email ou links (também aceita whatsapp, instagram, snapchat, discord)")
    texto: str = Field(description="Mensagem ou link recebido")


# Limite simples de pedidos por pessoa, para não estourar a cota gratuita da IA.
_pedidos_por_ip: dict[str, deque] = defaultdict(deque)


def _verificar_limite(ip: str, grupo: str = "analisar") -> None:
    agora = time.monotonic()
    fila = _pedidos_por_ip[f"{grupo}:{ip}"]
    while fila and agora - fila[0] > 60:
        fila.popleft()
    if len(fila) >= config.LIMITE_POR_MINUTO:
        raise HTTPException(429, "Muitos pedidos seguidos. Espere um minuto e tente de novo.")
    fila.append(agora)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


@app.get("/health")
def health():
    """Disponibilidade básica do serviço e modo da consulta de vazamentos (demonstração ou real)."""
    return {"status": "ok", "vazamentos": vazamentos.estado_das_fontes(), "ia_configurada": gemini.configurado()}


@app.post("/api/v1/check")
def verificar_exposicao(pedido: PedidoConsulta, request: Request):
    """Verifica se o e-mail e/ou telefone aparecem em vazamentos conhecidos. Nada é guardado."""
    _verificar_limite(_ip(request), "check")  # também dificulta enumeração em massa
    try:
        resultado = vazamentos.consultar(pedido.email, pedido.telefone)
    except vazamentos.EntradaInvalida as erro:
        raise HTTPException(422, str(erro)) from None
    if resultado["status"] == "nao_verificado" and resultado["falha_fonte"]:
        raise HTTPException(503, " ".join(resultado["avisos"]) + " Tente de novo em alguns minutos.")
    return resultado


@app.post("/api/v1/conversa")
def conversar(pedido: PedidoConversa, request: Request):
    """Chat para tirar dúvidas sobre golpes e phishing. Nada é guardado."""
    _verificar_limite(_ip(request), "conversa")
    try:
        return conversa.responder(pedido.historico, pedido.contexto)
    except conversa.EntradaInvalida as erro:
        raise HTTPException(422, str(erro)) from None


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

    _verificar_limite(_ip(request))
    return servico.analisar(plataforma, texto)


# ---------------------------------------------------------------------------
# Moderação dos casos reais (página admin.html). Sem senha, por decisão da equipe:
# só aceita pedidos feitos no próprio computador que roda o servidor.
# ---------------------------------------------------------------------------
HOSTS_LOCAIS = {"127.0.0.1", "::1", "localhost"}


def somente_local(request: Request) -> None:
    if _ip(request) not in HOSTS_LOCAIS:
        raise HTTPException(403, "A moderação só funciona no computador que roda o servidor.")


admin = [Depends(somente_local)]


def _erro_de_caso(erro: Exception):
    if isinstance(erro, casos.CasoNaoEncontrado):
        return HTTPException(404, "Caso não encontrado.")
    return HTTPException(422, str(erro))


@app.get("/api/v1/admin/opcoes", dependencies=admin)
def opcoes_de_moderacao():
    return casos.opcoes()


@app.get("/api/v1/admin/casos", dependencies=admin)
def listar_casos(status: str | None = Query(None), plataforma: str | None = Query(None),
                 busca: str | None = Query(None, max_length=100), limite: int = 50, deslocamento: int = 0):
    return casos.listar(status, plataforma, busca, limite, deslocamento)


@app.post("/api/v1/admin/casos", status_code=201, dependencies=admin)
def criar_caso(pedido: CasoEntrada):
    try:
        caso, ocultados = casos.criar(pedido.model_dump())
    except casos.CasoInvalido as erro:
        raise _erro_de_caso(erro) from None
    return {"caso": caso, "dados_ocultados": ocultados}


@app.post("/api/v1/admin/casos/sugestao", dependencies=admin)
def sugerir_caso(pedido: PedidoSugestao):
    try:
        return casos.sugerir(pedido.plataforma, pedido.texto)
    except casos.CasoInvalido as erro:
        raise _erro_de_caso(erro) from None


@app.get("/api/v1/admin/casos/{caso_id}", dependencies=admin)
def obter_caso(caso_id: int):
    try:
        return casos.obter(caso_id)
    except casos.CasoNaoEncontrado as erro:
        raise _erro_de_caso(erro) from None


@app.patch("/api/v1/admin/casos/{caso_id}", dependencies=admin)
def editar_caso(caso_id: int, pedido: CasoEdicao):
    try:
        caso, ocultados = casos.atualizar(caso_id, pedido.model_dump(exclude_unset=True))
    except (casos.CasoInvalido, casos.CasoNaoEncontrado) as erro:
        raise _erro_de_caso(erro) from None
    return {"caso": caso, "dados_ocultados": ocultados}


@app.delete("/api/v1/admin/casos/{caso_id}", status_code=204, dependencies=admin)
def excluir_caso(caso_id: int):
    try:
        casos.excluir(caso_id)
    except casos.CasoNaoEncontrado as erro:
        raise _erro_de_caso(erro) from None



@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/proj1.html")


# O site (HTML, CSS e JS) é servido pela própria API: tudo no mesmo endereço.
app.mount("/", StaticFiles(directory=config.PASTA_FRONTEND, html=True), name="site")
