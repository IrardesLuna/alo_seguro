"""Busca casos reais confirmados parecidos com a mensagem nova (aprendizado contínuo).

Hoje os casos vêm de agente/casos_reais/casos_confirmados.json.
Quando o CRUD de moderação existir, basta trocar a função carregar_casos()
para ler do banco de dados (ver agente/INTEGRACAO_CRUD.md).
"""
import json
import re

from .agente import REDES_SOCIAIS
from .config import PASTA_AGENTE
from .heuristica import jaccard, normalizar

ARQUIVO_CASOS = PASTA_AGENTE / "casos_reais" / "casos_confirmados.json"
MAXIMO_CASOS = 5
SEMELHANCA_MINIMA = 0.3
TAMANHO_MAXIMO_TEXTO = 500

PALAVRAS_VAZIAS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "que", "um", "uma", "para", "pra", "com", "em",
    "no", "na", "nos", "nas", "por", "se", "eu", "voce", "vc", "me", "te", "meu", "minha", "seu",
    "sua", "ao", "aos", "as", "os", "mais", "mas", "ja", "ta", "esta", "isso", "esse", "essa", "aqui",
}


def palavras_importantes(texto: str) -> set:
    palavras = re.findall(r"[a-z0-9]{3,}", normalizar(texto))
    return {p for p in palavras if p not in PALAVRAS_VAZIAS}


def carregar_casos() -> list[dict]:
    if not ARQUIVO_CASOS.exists():
        return []
    dados = json.loads(ARQUIVO_CASOS.read_text(encoding="utf-8"))
    return dados.get("casos", [])


def buscar(plataforma: str, taticas: set, texto: str, casos: list[dict] | None = None) -> list[dict]:
    """Devolve até 5 casos parecidos, com pelo menos 1 'nao_golpe' quando houver."""
    if casos is None:
        casos = carregar_casos()
    palavras_novas = palavras_importantes(texto)

    # "redes_sociais" aceita casos de qualquer rede (WhatsApp, Instagram, Facebook...).
    if plataforma in ("redes_sociais",) + REDES_SOCIAIS:
        aceitas = {"redes_sociais", *REDES_SOCIAIS}
    else:
        aceitas = {plataforma}

    candidatos = []
    for caso in casos:
        if caso.get("plataforma") not in aceitas or caso.get("reservado_para_teste"):
            continue
        semelhanca = (0.6 * jaccard(set(caso.get("taticas", [])), set(taticas))
                      + 0.4 * jaccard(palavras_importantes(caso.get("texto", "")), palavras_novas))
        if semelhanca >= SEMELHANCA_MINIMA:
            candidatos.append((semelhanca, caso))

    candidatos.sort(key=lambda par: par[0], reverse=True)
    escolhidos = candidatos[:MAXIMO_CASOS]

    tem_nao_golpe = any(caso.get("rotulo") == "nao_golpe" for _, caso in escolhidos)
    if not tem_nao_golpe and len(escolhidos) == MAXIMO_CASOS:
        for par in candidatos[MAXIMO_CASOS:]:
            if par[1].get("rotulo") == "nao_golpe":
                escolhidos[-1] = par
                break

    return [dict(caso, semelhanca=round(semelhanca, 2)) for semelhanca, caso in escolhidos]


def formatar_para_prompt(casos: list[dict]) -> str:
    if not casos:
        return "Nenhum caso similar ainda."
    blocos = []
    for caso in casos:
        texto = caso.get("texto", "")[:TAMANHO_MAXIMO_TEXTO]
        texto = texto.replace("<caso", "[caso").replace("</caso>", "[/caso]")
        blocos.append(
            f'<caso id="{caso.get("id")}" rotulo="{caso.get("rotulo")}" '
            f'golpe_base="{caso.get("golpe_base") or ""}" semelhanca="{caso["semelhanca"]}">\n'
            f"Texto: {texto}\n"
            f"Táticas: {', '.join(caso.get('taticas', []))}\n"
            f"Lição: {caso.get('licao') or '-'}\n"
            "</caso>"
        )
    return "\n".join(blocos)
