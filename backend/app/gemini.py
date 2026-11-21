"""Chamada à API do Google Gemini (REST), feita só pelo servidor.

A chave fica no backend/.env e nunca vai para o navegador.
"""
import json
import re
import time

import httpx

from . import config

URL_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiErro(Exception):
    """Erro com mensagem amigável para mostrar ao usuário."""


class _ModeloIndisponivel(GeminiErro):
    """Erro passageiro de um modelo: vale a pena tentar o próximo da lista."""


def configurado() -> bool:
    return bool(config.GEMINI_API_KEY)


def _extrair_json(texto: str) -> dict:
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto)  # remove ```json ... ``` se vier
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise GeminiErro("A IA respondeu num formato inesperado.")
    return json.loads(texto[inicio:fim + 1])


def _chamar_modelo(modelo: str, corpo: dict, tempo_limite: float) -> dict:
    url = f"{URL_BASE}/models/{modelo}:generateContent"
    cabecalhos = {"x-goog-api-key": config.GEMINI_API_KEY, "Content-Type": "application/json"}
    try:
        resposta = httpx.post(url, json=corpo, headers=cabecalhos, timeout=tempo_limite)
    except httpx.TimeoutException as erro:
        raise _ModeloIndisponivel("A IA demorou demais para responder.") from erro
    except httpx.HTTPError as erro:
        raise GeminiErro("Não foi possível conectar à IA.") from erro

    if resposta.status_code in (500, 502, 503, 504):
        raise _ModeloIndisponivel("A IA está sobrecarregada no momento. Tente de novo em alguns minutos.")
    if resposta.status_code == 429:
        raise _ModeloIndisponivel("O limite gratuito da IA foi atingido. Tente de novo em alguns minutos.")
    if resposta.status_code == 404:
        raise _ModeloIndisponivel(f"O modelo '{modelo}' não existe para esta chave. "
                                  "Rode 'python -m app.listar_modelos' para ver os disponíveis.")
    if resposta.status_code == 403 and "free tier" in resposta.text.lower():
        raise GeminiErro("O Google não liberou o plano gratuito da IA para o projeto desta chave "
                         "(veja 'Problemas com a chave do Gemini' no README).")
    if resposta.status_code in (400, 401, 403) and "api key" in resposta.text.lower():
        raise GeminiErro("A chave da IA é inválida. Confira o valor de GEMINI_API_KEY no backend/.env.")
    if resposta.status_code in (401, 403):
        raise GeminiErro("A chave da IA não tem permissão.")
    if resposta.status_code >= 400:
        raise GeminiErro(f"A IA devolveu um erro ({resposta.status_code}).")
    return resposta.json()


def _ler_resposta(dados: dict) -> dict:
    try:
        candidato = dados["candidates"][0]
        partes = candidato["content"]["parts"]
        texto = "".join(parte.get("text", "") for parte in partes if not parte.get("thought"))
    except (KeyError, IndexError) as erro:
        motivo = dados.get("promptFeedback", {}).get("blockReason")
        if motivo:
            raise GeminiErro("A IA se recusou a analisar este conteúdo.") from erro
        raise _ModeloIndisponivel("A IA não devolveu uma resposta.") from erro
    try:
        return _extrair_json(texto)
    except (json.JSONDecodeError, GeminiErro) as erro:
        raise _ModeloIndisponivel("A IA respondeu num formato inválido.") from erro


def gerar_json(prompt_sistema: str, mensagem_usuario: str, esquema: dict | None = None,
               tempo_maximo: float | None = None) -> dict:
    if not configurado():
        raise GeminiErro("A chave da IA não está configurada no servidor.")

    configuracao = {"temperature": 0.2, "responseMimeType": "application/json"}
    if esquema:
        configuracao["responseSchema"] = esquema  # obriga a IA a seguir o formato combinado
    corpo = {
        "system_instruction": {"parts": [{"text": prompt_sistema}]},
        "contents": [{"role": "user", "parts": [{"text": mensagem_usuario}]}],
        "generationConfig": configuracao,
    }

    # Tenta cada modelo da lista; passa para o próximo só em erros passageiros
    # (sobrecarga, limite, modelo inexistente ou resposta ilegível).
    # Tudo isso respeita um tempo máximo total, para a pessoa não ficar esperando demais.
    ultimo_erro = None
    prazo_final = time.monotonic() + (tempo_maximo or config.GEMINI_TEMPO_MAXIMO)
    for rodada in range(config.GEMINI_RODADAS):
        if rodada > 0:
            time.sleep(config.GEMINI_ESPERA_SEGUNDOS)  # picos de uso costumam passar rápido
        for posicao, modelo in enumerate(config.GEMINI_MODELOS):
            tempo_restante = prazo_final - time.monotonic()
            if tempo_restante < 3:
                raise GeminiErro("A IA demorou demais para responder.")
            # Um modelo travado não pode gastar o prazo todo: se ainda há outro para tentar,
            # ele fica com no máximo 60% do tempo que sobra (no plano gratuito, o modelo
            # principal costuma ficar sobrecarregado e o reserva responde rápido).
            ultima_chance = rodada == config.GEMINI_RODADAS - 1 and posicao == len(config.GEMINI_MODELOS) - 1
            limite = tempo_restante if ultima_chance else tempo_restante * 0.6
            try:
                return _ler_resposta(_chamar_modelo(modelo, corpo, min(config.GEMINI_TIMEOUT, limite)))
            except _ModeloIndisponivel as erro:
                ultimo_erro = erro
    raise GeminiErro(str(ultimo_erro))


def listar_modelos() -> list[str]:
    resposta = httpx.get(f"{URL_BASE}/models", headers={"x-goog-api-key": config.GEMINI_API_KEY},
                         params={"pageSize": 200}, timeout=30)
    resposta.raise_for_status()
    modelos = []
    for modelo in resposta.json().get("models", []):
        if "generateContent" in modelo.get("supportedGenerationMethods", []):
            modelos.append(modelo["name"].removeprefix("models/"))
    return modelos
