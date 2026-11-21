"""Conversa Segura: chat para tirar dúvidas sobre golpes e phishing (POST /api/v1/conversa).

O servidor não guarda a conversa: o navegador manda o histórico a cada pergunta e ele some
quando a página fecha. Antes de ir para a IA, cada fala da pessoa passa pela anonimização.

Fluxo de cada resposta:
1. valida o histórico (tamanho, número de falas, última fala é da pessoa);
2. anonimiza as falas e roda as regras automáticas (heuristica.py) na última;
3. com IA: o agente (agente/prompt_conversa.md) responde e o backend confere a resposta
   (tira links e telefones, não deixa o risco cair abaixo do que as regras acharam);
4. sem IA (ou se ela falhar): resposta montada pelas regras.
"""
import re

from . import agente, config, gemini, heuristica
from .anonimizar import PADROES, anonimizar
from .links import REGEX_URL

MAXIMO_FALAS = 12                 # 6 perguntas e 6 respostas por conversa
TAMANHO_MAXIMO_FALA = 2000
TAMANHO_MAXIMO_RESPOSTA = 1200
NIVEIS = ("baixo", "medio", "alto", "muito_alto")
ORDEM_NIVEL = {"sem_avaliacao": -1, "baixo": 0, "medio": 1, "alto": 2, "muito_alto": 3}

AJUDA = heuristica.AJUDA
SE_JA_CAIU = heuristica.SE_JA_CAIU

SUGESTOES_INICIAIS = [
    "Recebi uma mensagem estranha",
    "Acho que caí em um golpe",
    "Como saber se um link é seguro?",
]

# Domínios que a IA pode citar (sites oficiais do governo).
_DOMINIO_PERMITIDO = re.compile(r"(^|\.)gov\.br$", re.IGNORECASE)
_TELEFONE = next(padrao for marcador, padrao in PADROES if marcador == "[TELEFONE]")

# Intenções reconhecidas pelas regras (texto sem acentos e minúsculo).
_JA_CAIU = re.compile(r"\b(ja (paguei|fiz|transferi|mandei|enviei|passei|cliquei|instalei|baixei|depositei)|"
                      r"cai (no|num|em um|em) golpe|cai no|fui (enganad|golpead)|me (golpearam|enganaram)|"
                      r"e agora)\b")
_SIMPLES = re.compile(r"\b(mais (simples|facil)|nao entendi|explica de novo|explique de novo|nao sei o que)\b")
_BANCO = re.compile(r"\bbanco\b.{0,40}\b(falar|ligar|contato|contatar|atendimento|seguranca)|"
                    r"\b(falar|ligar|contato|contatar)\b.{0,40}\bbanco\b")
_DUAS_ETAPAS = re.compile(r"\b(duas etapas|dois fatores|2fa|verificacao em duas)\b")
_LINK_SEGURO = re.compile(r"\b(link|site|endereco)\b.{0,40}\b(seguro|confiavel|verdadeiro|oficial|golpe|falso)\b")
_MENSAGEM_ESTRANHA = re.compile(r"\b(mensagem|email|e-mail|sms|ligacao|ligaram|recebi)\b")


class EntradaInvalida(ValueError):
    """Erro de validação com mensagem para mostrar na tela."""


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def validar_historico(historico: list[dict]) -> list[dict]:
    if not historico:
        raise EntradaInvalida("Escreva sua dúvida para começar.")
    if len(historico) > MAXIMO_FALAS:
        raise EntradaInvalida("Esta conversa chegou ao limite. Comece uma nova conversa.")
    limpo = []
    for fala in historico:
        papel = fala.get("papel")
        texto = str(fala.get("texto") or "").strip()
        if papel not in ("usuario", "assistente"):
            raise EntradaInvalida("Formato da conversa inválido.")
        if papel == "usuario":
            if not texto:
                raise EntradaInvalida("Escreva sua dúvida.")
            if len(texto) > TAMANHO_MAXIMO_FALA:
                raise EntradaInvalida(f"Mensagem muito longa. Escreva até {TAMANHO_MAXIMO_FALA} caracteres.")
        limpo.append({"papel": papel, "texto": texto[:TAMANHO_MAXIMO_RESPOSTA if papel == "assistente" else TAMANHO_MAXIMO_FALA]})
    if limpo[-1]["papel"] != "usuario":
        raise EntradaInvalida("A última mensagem da conversa precisa ser sua.")
    return limpo


def validar_contexto(contexto: dict | None) -> dict | None:
    """Resumo da análise de mensagem que a pessoa acabou de fazer (opcional). Só campos conhecidos."""
    if not isinstance(contexto, dict):
        return None
    try:
        nota = max(1, min(99, int(contexto.get("probabilidade_golpe"))))
    except (TypeError, ValueError):
        nota = None
    nivel = contexto.get("nivel") if contexto.get("nivel") in NIVEIS else None
    taticas_validas = agente.taticas_por_id()
    taticas = [t for t in contexto.get("taticas") or [] if t in taticas_validas][:8]
    limpo = {
        "probabilidade_golpe": nota,
        "nivel": nivel,
        "veredito": str(contexto.get("veredito") or "")[:200],
        "golpe_parecido": str(contexto.get("golpe_parecido") or "")[:120],
        "taticas": [taticas_validas[t]["nome"] for t in taticas],
    }
    return limpo if (nota or nivel or limpo["veredito"]) else None


# ---------------------------------------------------------------------------
# Conferência da resposta da IA
# ---------------------------------------------------------------------------
def _dominio(url: str) -> str:
    sem_protocolo = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    return sem_protocolo.split("/")[0].split(":")[0].lower().rstrip(".")


def limpar_resposta(texto: str) -> str:
    """Remove links (menos .gov.br) e telefones que a IA tenha escrito."""
    def trocar_link(achado):
        url = achado.group(0)
        return url if _DOMINIO_PERMITIDO.search(_dominio(url)) else "[link removido]"
    texto = REGEX_URL.sub(trocar_link, texto)
    texto = _TELEFONE.sub("[número removido: use o canal oficial]", texto)
    return texto.strip()[:TAMANHO_MAXIMO_RESPOSTA]


def _sugestoes(valor) -> list[str]:
    sugestoes = []
    for item in valor if isinstance(valor, list) else []:
        texto = limpar_resposta(str(item or ""))[:60].strip()
        if texto and "[" not in texto and texto not in sugestoes:
            sugestoes.append(texto)
    return sugestoes[:3]


# ---------------------------------------------------------------------------
# Resposta por regras (sem IA)
# ---------------------------------------------------------------------------
def _lista(itens: list[str]) -> str:
    return "\n".join(f"- {item}" for item in itens)


def resposta_por_regras(historico: list[dict], regras: dict, contexto: dict | None) -> dict:
    ultima = heuristica.normalizar(historico[-1]["texto"])
    taticas = regras["taticas_detectadas"]
    nivel = regras["nivel"] if taticas else "sem_avaliacao"

    if _JA_CAIU.search(ultima) or regras["se_ja_caiu"]:
        texto = ("Calma, dá para agir. Faça isto agora, na ordem:\n" + _lista(SE_JA_CAIU[:4])
                 + "\nVocê não tem culpa: golpistas são profissionais em enganar.")
        sugestoes = ["Como falo com meu banco com segurança?", "O que é o MED do Pix?", "Explica de um jeito mais simples"]
        nivel = "alto" if nivel == "sem_avaliacao" else nivel
    elif taticas:
        nomes = [agente.taticas_por_id()[t]["nome"].lower() for t in taticas[:3]]
        # Sem o "parece o golpe X": em falas curtas a comparação com a base erra muito.
        veredito = regras["veredito"].split(" Parece o ")[0]
        texto = (f"{veredito} Encontrei estes sinais: {', '.join(nomes)}.\n"
                 + _lista([f["explicacao"] for f in regras["red_flags"][:2]] + regras["dicas"][:2]))
        sugestoes = ["Já paguei ou cliquei. E agora?", "Como confirmo se é verdade?", "Explica de um jeito mais simples"]
    elif _BANCO.search(ultima):
        texto = ("Para falar com o banco com segurança:\n"
                 + _lista(["Use o app oficial do banco ou o telefone que está no verso do seu cartão.",
                           "Nunca ligue para um número que veio na mensagem, no SMS ou no e-mail.",
                           "Se puder, ligue de outro telefone: golpistas às vezes mantêm a linha presa.",
                           "O banco nunca pede senha, código ou para transferir para uma \"conta segura\"."]))
        sugestoes = ["O que é o MED do Pix?", "Recebi uma ligação do banco", "Acho que caí em um golpe"]
    elif _DUAS_ETAPAS.search(ultima):
        texto = ("A verificação em duas etapas pede um segundo código além da senha. Assim, mesmo quem "
                 "descobrir sua senha não entra na conta. No WhatsApp:\n"
                 + _lista(["Abra Configurações (ou Ajustes).", "Toque em Conta.",
                           "Toque em Confirmação em duas etapas e depois em Ativar.",
                           "Crie um PIN de 6 números que só você sabe e cadastre um e-mail."]))
        sugestoes = ["E no Instagram?", "Recebi um código que não pedi", "Explica de um jeito mais simples"]
    elif _LINK_SEGURO.search(ultima):
        texto = ("Antes de clicar, olhe o endereço com calma:\n"
                 + _lista(["Veja o nome logo antes do primeiro \"/\": é ele que diz de quem é o site.",
                           "Desconfie de letras trocadas, palavras a mais (\"-oficial\", \"-promo\") e finais como .shop ou .xyz.",
                           "Sites do governo terminam em .gov.br.",
                           "Na dúvida, não clique: abra o app oficial ou digite o endereço você mesmo."])
                 + "\nSe quiser, cole o link aqui que eu olho com você.")
        sugestoes = ["Já cliquei no link. E agora?", "Recebi uma mensagem estranha", "Explica de um jeito mais simples"]
    elif _SIMPLES.search(ultima):
        texto = ("Em poucas palavras: quem pede dinheiro, código, senha ou para clicar com pressa provavelmente "
                 "é golpista. Antes de fazer qualquer coisa, pare e confirme com a pessoa ou a empresa por um "
                 "canal que você já conhece, como o número salvo na agenda ou o app oficial.")
        sugestoes = ["Recebi uma mensagem estranha", "Acho que caí em um golpe", "Como falo com meu banco com segurança?"]
    elif contexto and contexto.get("nivel") in ("alto", "muito_alto"):
        texto = ("Na análise que você fez, a mensagem teve risco " + contexto["nivel"].replace("_", " ")
                 + ". O mais seguro é não responder, não clicar e não pagar. Confirme por um canal que você já conhece.")
        sugestoes = ["Já paguei ou cliquei. E agora?", "Como confirmo se é verdade?", "Explica de um jeito mais simples"]
        nivel = contexto["nivel"]
    elif _MENSAGEM_ESTRANHA.search(ultima):
        texto = ("Posso te ajudar a avaliar. Cole aqui o texto da mensagem (pode apagar seus dados pessoais) "
                 "ou me conte: quem mandou e o que estão pedindo? Dinheiro, código, clique em link ou seus dados?")
        sugestoes = ["Pediram um código que chegou por SMS", "Pediram um Pix urgente", "Mandaram um link para clicar"]
    else:
        texto = ("Não encontrei sinais claros de golpe no que você escreveu. Me conte mais: quem entrou em contato, "
                 "por onde (WhatsApp, e-mail, ligação) e o que pediram?")
        sugestoes = list(SUGESTOES_INICIAIS)

    return {"resposta": texto, "nivel_risco": nivel, "sugestoes": sugestoes}


# ---------------------------------------------------------------------------
# Resposta
# ---------------------------------------------------------------------------
def responder(historico: list[dict], contexto: dict | None = None) -> dict:
    historico = validar_historico(historico)
    contexto = validar_contexto(contexto)

    dados_ocultados = 0
    anonimizado = []
    for fala in historico:
        texto, quantidade = anonimizar(fala["texto"]) if fala["papel"] == "usuario" else (fala["texto"], 0)
        dados_ocultados += quantidade if fala is historico[-1] else 0
        anonimizado.append({"papel": fala["papel"], "texto": texto})

    regras = heuristica.analisar("redes_sociais", anonimizado[-1]["texto"])
    risco_pelas_regras = regras["nivel"] if regras["taticas_detectadas"] else "sem_avaliacao"
    ajuda_pelas_regras = regras["aviso_ajuda"] is not None

    origem, aviso_sistema = "regras", None
    resultado = None
    if gemini.configurado():
        try:
            pre_analise = {
                "observacao": "Sinais encontrados por regras simples na última fala. Podem ter falsos positivos.",
                "taticas": [{"tatica": t, "trecho": trecho} for t, trecho in regras["_evidencias"].items()],
                "nota_das_regras": regras["probabilidade_golpe"] if regras["taticas_detectadas"] else None,
                "links": regras["analise_link"],
                "dados_pessoais_ocultados": dados_ocultados,
            }
            bruto = gemini.gerar_json(agente.montar_prompt_conversa(),
                                      agente.montar_mensagem_conversa(anonimizado, pre_analise, contexto),
                                      agente.ESQUEMA_CONVERSA, tempo_maximo=25)
            texto = limpar_resposta(str(bruto.get("resposta") or ""))
            if not texto:
                raise gemini.GeminiErro("A IA não devolveu uma resposta.")
            nivel = bruto.get("nivel_risco") if bruto.get("nivel_risco") in ORDEM_NIVEL else "sem_avaliacao"
            # Segurança: em caso grave achado pelas regras, a IA não pode baixar o risco.
            if risco_pelas_regras in ("alto", "muito_alto") and ORDEM_NIVEL[nivel] < ORDEM_NIVEL[risco_pelas_regras]:
                nivel = risco_pelas_regras
            resultado = {"resposta": texto, "nivel_risco": nivel,
                         "sugestoes": _sugestoes(bruto.get("sugestoes")) or list(SUGESTOES_INICIAIS)}
            ajuda_pela_ia = bool(bruto.get("precisa_ajuda"))
            origem = "ia"
        except gemini.GeminiErro as erro:
            aviso_sistema = f"{erro} Respondi com as regras automáticas, que entendem menos o contexto."
    else:
        aviso_sistema = "A IA não está configurada neste servidor. Respondi com as regras automáticas, que entendem menos o contexto."

    if resultado is None:
        resultado = resposta_por_regras(anonimizado, regras, contexto)
        ajuda_pela_ia = False

    falas_restantes = (MAXIMO_FALAS - len(historico) - 1) // 2
    resultado.update({
        "aviso_ajuda": AJUDA if (ajuda_pelas_regras or ajuda_pela_ia) else None,
        "origem": origem,
        "aviso_sistema": aviso_sistema,
        "dados_ocultados": dados_ocultados,
        "perguntas_restantes": max(0, falas_restantes),
    })
    return resultado
