"""Junta as peças: anonimização, regras, casos parecidos e IA."""
from . import agente, gemini, heuristica, similares
from .anonimizar import anonimizar

NIVEIS = ("baixo", "medio", "alto", "muito_alto")
TIPOS_DE_LINK = ("legitimo_provavel", "loja_falsa", "roubo_de_dados", "download_malicioso",
                 "fraude_financeira", "indeterminado")


def _texto(valor, limite: int = 600) -> str:
    return str(valor).strip()[:limite] if valor is not None else ""


def _lista_de_textos(valor, maximo: int = 8) -> list[str]:
    if not isinstance(valor, list):
        return []
    textos = []
    for item in valor:
        if isinstance(item, dict):  # ex.: {"passo_1": "..."} vira só o texto
            item = " ".join(str(v) for v in item.values() if v)
        if _texto(item):
            textos.append(_texto(item))
    return textos[:maximo]


def normalizar_resultado(bruto: dict, plataforma: str, regras: dict) -> dict:
    """Confere e corrige a resposta da IA para nunca quebrar a tela."""
    try:
        nota = int(round(float(bruto.get("probabilidade_golpe", regras["probabilidade_golpe"]))))
    except (TypeError, ValueError):
        nota = regras["probabilidade_golpe"]
    nota = max(1, min(99, nota))  # regra do projeto: nunca 0% e nunca 100%

    taticas_validas = agente.taticas_por_id()
    taticas = [t for t in bruto.get("taticas_detectadas", []) if t in taticas_validas]

    red_flags = []
    for item in bruto.get("red_flags", []) if isinstance(bruto.get("red_flags"), list) else []:
        if isinstance(item, dict) and _texto(item.get("explicacao")):
            tatica = item.get("tatica") if item.get("tatica") in taticas_validas else None
            red_flags.append({"trecho": _texto(item.get("trecho"), 200), "tatica": tatica,
                              "explicacao": _texto(item.get("explicacao"))})

    parecido = bruto.get("golpe_parecido")
    if isinstance(parecido, dict) and parecido.get("id") in agente.golpes_por_id():
        golpe = agente.golpes_por_id()[parecido["id"]]
        try:
            similaridade = max(0, min(100, int(parecido.get("similaridade", 0))))
        except (TypeError, ValueError):
            similaridade = 0
        parecido = {"id": golpe["id"], "nome": golpe["nome"], "similaridade": similaridade}
    else:
        parecido = None

    links = []
    for item in bruto.get("analise_link", []) if isinstance(bruto.get("analise_link"), list) else []:
        if isinstance(item, dict) and item.get("url"):
            links.append({"url": _texto(item["url"], 300), "dominio_real": _texto(item.get("dominio_real"), 120),
                          "tipo": item.get("tipo") if item.get("tipo") in TIPOS_DE_LINK else "indeterminado",
                          "motivos": _lista_de_textos(item.get("motivos"))})
    if not links:
        links = regras["analise_link"]  # a IA esqueceu os links: usamos a análise técnica

    # Sempre pelo menos 3 dicas de como confirmar: se a IA mandou poucas, completamos.
    dicas = _lista_de_textos(bruto.get("dicas"), maximo=6)
    for dica in regras["dicas"]:
        if len(dicas) >= 3:
            break
        if dica not in dicas:
            dicas.append(dica)

    return {
        "probabilidade_golpe": nota,
        "nivel": heuristica._nivel(nota),
        "confianca_analise": bruto.get("confianca_analise") if bruto.get("confianca_analise") in ("baixa", "media", "alta") else "media",
        "veredito": _texto(bruto.get("veredito"), 200) or regras["veredito"],
        "explicacao": _texto(bruto.get("explicacao"), 900) or regras["explicacao"],
        "canal_analisado": _texto(bruto.get("canal_analisado"), 20) or plataforma,
        "golpe_parecido": parecido,
        "taticas_detectadas": taticas,
        "red_flags": red_flags[:6],
        "sinais_de_legitimidade": _lista_de_textos(bruto.get("sinais_de_legitimidade")),
        "dicas": dicas,
        "se_ja_caiu": _lista_de_textos(bruto.get("se_ja_caiu")),
        "analise_link": links,
        "aviso_ajuda": _texto(bruto.get("aviso_ajuda"), 400) or None,
        "possivel_golpe_novo": bool(bruto.get("possivel_golpe_novo")),
        "observacoes": _texto(bruto.get("observacoes"), 400) or None,
    }


def _pre_analise(regras: dict, dados_ocultados: int) -> dict:
    return {
        "observacao": "Sinais encontrados por regras simples. Podem ter falsos positivos: confirme no texto.",
        "taticas_sugeridas": [{"tatica": t, "trecho": trecho} for t, trecho in regras["_evidencias"].items()],
        "nota_das_regras": regras["probabilidade_golpe"],
        "links": regras["_links"],
        "dados_pessoais_ocultados": dados_ocultados,
    }


def analisar(plataforma: str, texto: str) -> dict:
    texto_anonimizado, dados_ocultados = anonimizar(texto)
    regras = heuristica.analisar(plataforma, texto_anonimizado)
    casos = similares.buscar(plataforma, set(regras["taticas_detectadas"]), texto_anonimizado)

    origem = "regras"
    aviso_sistema = None
    if gemini.configurado():
        try:
            prompt = agente.montar_prompt_sistema(plataforma, similares.formatar_para_prompt(casos))
            mensagem = agente.montar_mensagem_usuario(texto_anonimizado, _pre_analise(regras, dados_ocultados))
            bruto = gemini.gerar_json(prompt, mensagem, agente.ESQUEMA_RESPOSTA)
            resultado = normalizar_resultado(bruto, plataforma, regras)
            origem = "ia"
        except gemini.GeminiErro as erro:
            aviso_sistema = f"{erro} Esta análise foi feita só com as regras automáticas e pode ser menos precisa."
    else:
        aviso_sistema = ("A IA não está configurada neste servidor. Esta análise foi feita só com as regras "
                         "automáticas e pode ser menos precisa.")

    if origem == "regras":
        resultado = {chave: valor for chave, valor in regras.items() if not chave.startswith("_")}

    nomes = agente.taticas_por_id()
    resultado["taticas_info"] = [
        {"id": t, "nome": nomes[t]["nome"], "peso": nomes[t]["peso"]} for t in resultado["taticas_detectadas"]
    ]
    resultado["origem"] = origem
    resultado["aviso_sistema"] = aviso_sistema
    resultado["dados_ocultados"] = dados_ocultados
    resultado["casos_usados"] = len(casos)
    return resultado
