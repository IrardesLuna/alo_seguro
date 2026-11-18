"""Oculta dados pessoais antes de mandar o texto para a IA (LGPD).

Os links são preservados, porque o domínio é essencial para detectar golpes.
"""
import re

from .links import REGEX_URL

# A ordem importa: padrões mais específicos primeiro.
PADROES = [
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("[CHAVE_PIX]", re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")),
    ("[CNPJ]", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    ("[CPF]", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("[CARTAO]", re.compile(r"\b(?:\d{4}[ .-]?){3}\d{4}\b")),
    ("[TELEFONE]", re.compile(r"(?:\+?55[\s-]?)?\(?\b\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}\b")),
    ("[CONTA]", re.compile(r"\b(?:ag(?:[eê]ncia)?\.?|conta|c/c|cc)\s*:?\s*\d[\d.-]{2,}", re.IGNORECASE)),
    # @perfis são mantidos: o perfil do golpista ("@suporte.nubank.oficial") ajuda a detectar o golpe.
]


def _anonimizar_trecho(trecho: str) -> tuple[str, int]:
    total = 0
    for marcador, padrao in PADROES:
        trecho, quantidade = padrao.subn(marcador, trecho)
        total += quantidade
    return trecho, total


def anonimizar(texto: str) -> tuple[str, int]:
    """Devolve (texto_anonimizado, quantidade_de_dados_ocultados)."""
    partes = []
    total = 0
    posicao = 0
    for link in REGEX_URL.finditer(texto):
        trecho, quantidade = _anonimizar_trecho(texto[posicao:link.start()])
        partes.append(trecho)
        partes.append(link.group(0))  # o link fica intacto
        total += quantidade
        posicao = link.end()
    trecho, quantidade = _anonimizar_trecho(texto[posicao:])
    partes.append(trecho)
    total += quantidade
    return "".join(partes), total
