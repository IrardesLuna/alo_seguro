"""Carrega a base de conhecimento (pasta agente/) e monta o prompt enviado à IA."""
import json
from datetime import date
from functools import lru_cache

from .config import PASTA_AGENTE

# Arquivos da base de conhecimento (agente/base_golpes/<id>.json)
BASES = {
    "whatsapp": "WhatsApp",
    "instagram": "Instagram",
    "snapchat": "Snapchat",
    "discord": "Discord",
    "email": "E-mail",
    "links": "Link",
}
REDES_SOCIAIS = ("whatsapp", "instagram", "snapchat", "discord")

# As 3 opções da tela "O que você quer analisar?"
CANAIS = {
    "redes_sociais": "Mensagem de rede social",
    "email": "E-mail",
    "links": "Link",
}

# Tudo o que a API aceita: as 3 opções da tela + cada rede social separada (útil para testes).
PLATAFORMAS = {**CANAIS, **{rede: BASES[rede] for rede in REDES_SOCIAIS}}

DESCRICAO_CANAL = {
    "redes_sociais": "mensagem de rede social ou aplicativo de conversa (WhatsApp, Instagram, Facebook, "
                     "LinkedIn, Telegram, TikTok, Snapchat, Discord, SMS ou outra; descubra qual pelo texto)",
    "email": "e-mail",
    "links": "link",
}

# Formato obrigatório da resposta da IA (o Gemini segue este esquema à risca).
_TEXTO = {"type": "STRING"}
_LISTA_DE_TEXTOS = {"type": "ARRAY", "items": _TEXTO}
CAMPOS_RESPOSTA = [
    "probabilidade_golpe", "nivel", "confianca_analise", "veredito", "explicacao", "canal_analisado",
    "golpe_parecido", "taticas_detectadas", "red_flags", "sinais_de_legitimidade", "dicas",
    "se_ja_caiu", "analise_link", "aviso_ajuda", "possivel_golpe_novo", "observacoes",
]
ESQUEMA_RESPOSTA = {
    "type": "OBJECT",
    "properties": {
        "probabilidade_golpe": {"type": "INTEGER"},
        "nivel": {"type": "STRING", "enum": ["baixo", "medio", "alto", "muito_alto"]},
        "confianca_analise": {"type": "STRING", "enum": ["baixa", "media", "alta"]},
        "veredito": _TEXTO,
        "explicacao": _TEXTO,
        "canal_analisado": _TEXTO,
        "golpe_parecido": {
            "type": "OBJECT", "nullable": True,
            "properties": {"id": _TEXTO, "nome": _TEXTO, "similaridade": {"type": "INTEGER"}},
        },
        "taticas_detectadas": _LISTA_DE_TEXTOS,
        "red_flags": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {"trecho": _TEXTO, "tatica": _TEXTO, "explicacao": _TEXTO},
            "required": ["trecho", "tatica", "explicacao"],
        }},
        "sinais_de_legitimidade": _LISTA_DE_TEXTOS,
        "dicas": {"type": "ARRAY", "items": _TEXTO, "minItems": 3, "maxItems": 6},
        "se_ja_caiu": _LISTA_DE_TEXTOS,
        "analise_link": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "url": _TEXTO, "dominio_real": _TEXTO,
                "tipo": {"type": "STRING", "enum": ["legitimo_provavel", "loja_falsa", "roubo_de_dados",
                                                    "download_malicioso", "fraude_financeira", "indeterminado"]},
                "motivos": _LISTA_DE_TEXTOS,
            },
            "required": ["url", "dominio_real", "tipo", "motivos"],
        }},
        "aviso_ajuda": {"type": "STRING", "nullable": True},
        "possivel_golpe_novo": {"type": "BOOLEAN"},
        "observacoes": {"type": "STRING", "nullable": True},
    },
    "required": CAMPOS_RESPOSTA,
    "propertyOrdering": CAMPOS_RESPOSTA,
}

MARCA_INICIO = "=== INÍCIO DO PROMPT ==="
MARCA_FIM = "=== FIM DO PROMPT ==="


@lru_cache
def taxonomia() -> dict:
    return json.loads((PASTA_AGENTE / "taxonomia.json").read_text(encoding="utf-8"))


@lru_cache
def taticas_por_id() -> dict:
    return {t["id"]: t for t in taxonomia()["taticas"]}


@lru_cache
def _arquivo_base(base: str) -> str:
    return (PASTA_AGENTE / "base_golpes" / f"{base}.json").read_text(encoding="utf-8")


@lru_cache
def base_golpes(plataforma: str) -> list[dict]:
    """Golpes de uma base. 'redes_sociais' junta WhatsApp, Instagram, Snapchat e Discord."""
    if plataforma == "redes_sociais":
        todos = []
        for rede in REDES_SOCIAIS:
            todos += base_golpes(rede)
        return todos
    return json.loads(_arquivo_base(plataforma))["golpes"]


@lru_cache
def base_texto(plataforma: str) -> str:
    """Base do jeito que vai para o prompt.

    Para redes sociais (409 golpes) usamos um formato enxuto, uma linha por golpe,
    para o prompt não ficar grande demais: id | nome | táticas | sinais.
    """
    if plataforma != "redes_sociais":
        return _arquivo_base(plataforma)
    linhas = ["id | nome | táticas | sinais"]
    for golpe in base_golpes("redes_sociais"):
        linhas.append(f"{golpe['id']} | {golpe['nome']} | {', '.join(golpe['taticas'])} | {'; '.join(golpe['sinais'])}")
    return "\n".join(linhas)


@lru_cache
def golpes_por_id() -> dict:
    todos = {}
    for base in BASES:
        for golpe in base_golpes(base):
            todos[golpe["id"]] = golpe
    return todos


@lru_cache
def _modelo_prompt(nome_arquivo: str) -> str:
    texto = (PASTA_AGENTE / nome_arquivo).read_text(encoding="utf-8")
    inicio = texto.rfind(MARCA_INICIO)
    fim = texto.rfind(MARCA_FIM)
    if inicio == -1 or fim == -1:
        raise ValueError(f"{nome_arquivo} não tem as marcas de início e fim do prompt")
    return texto[inicio + len(MARCA_INICIO):fim].strip()


def montar_prompt_sistema(plataforma: str, casos_similares: str) -> str:
    substituicoes = {
        "{{PLATAFORMA}}": DESCRICAO_CANAL.get(plataforma, plataforma),
        "{{BASE_DE_GOLPES}}": base_texto(plataforma),
        "{{CASOS_SIMILARES}}": casos_similares or "Nenhum caso similar ainda.",
        "{{DATA_ATUAL}}": date.today().strftime("%d/%m/%Y"),
    }
    prompt = _modelo_prompt("prompt_sistema.md")
    for marcador, valor in substituicoes.items():
        prompt = prompt.replace(marcador, valor)
    return prompt


def montar_mensagem_usuario(texto: str, pre_analise: dict) -> str:
    # Impede que o texto colado "feche" as tags e finja ser instrução.
    texto_seguro = (texto.replace("<mensagem_recebida>", "[mensagem_recebida]")
                    .replace("</mensagem_recebida>", "[/mensagem_recebida]")
                    .replace("<pre_analise_automatica>", "[pre_analise_automatica]")
                    .replace("</pre_analise_automatica>", "[/pre_analise_automatica]"))
    return (
        "<pre_analise_automatica>\n"
        + json.dumps(pre_analise, ensure_ascii=False, indent=1)
        + "\n</pre_analise_automatica>\n\n<mensagem_recebida>\n"
        + texto_seguro
        + "\n</mensagem_recebida>"
    )
