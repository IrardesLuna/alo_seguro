"""Análise técnica de links, feita pelo código (sem IA).

O resultado vai para a IA como "pré-análise" e também é usado quando a IA está fora do ar.
Nenhum link é acessado: olhamos só o texto do endereço.
"""
import ipaddress
import re
from urllib.parse import parse_qs, urlsplit

REGEX_URL = re.compile(
    r"(?:https?://|www\.)[^\s<>\"'()]+"
    r"|(?<![@\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|br|xyz|top|shop|click|online|site|live|icu|buzz|store|vip|club|info|"
    r"app|link|ly|gl|me|io|co|gg|tk|ml|cf|ga|gq|pw|cfd|sbs|bond|cyou|lol|fun|work|rest)"
    r"(?:/[^\s<>\"'()]*)?",
    re.IGNORECASE,
)

ENCURTADORES = {
    "bit.ly", "bitly.com", "tinyurl.com", "cutt.ly", "is.gd", "t.co", "ow.ly", "rebrand.ly",
    "shorturl.at", "rb.gy", "t.ly", "s.id", "abre.ai", "encurtador.com.br", "l1nq.com",
    "tiny.cc", "goo.gl", "bit.do", "v.gd", "short.io",
}

EXTENSOES_SUSPEITAS = {
    "xyz", "top", "shop", "click", "online", "site", "live", "icu", "buzz", "vip", "club",
    "work", "fun", "lol", "cyou", "bond", "cfd", "sbs", "rest", "pw", "tk", "ml", "ga", "cf", "gq",
}

HOSPEDAGEM_GENERICA = (
    "sites.google.com", "github.io", "web.app", "firebaseapp.com", "netlify.app", "vercel.app",
    "pages.dev", "glitch.me", "canva.site", "wixsite.com", "blogspot.com", "weebly.com",
    "000webhostapp.com", "forms.gle", "carrd.co", "framer.website", "webflow.io",
)

SUFIXOS_DUPLOS = ("com.br", "gov.br", "org.br", "net.br", "edu.br", "bet.br", "art.br", "co.uk", "com.ar")

DOWNLOADS = (".apk", ".exe", ".scr", ".msi", ".bat", ".cmd", ".zip", ".rar", ".iso", ".vbs", ".jar")

PALAVRAS_LOGIN = ("login", "signin", "entrar", "verifica", "atualiza", "token", "senha", "seguranca",
                  "conta", "auth", "acesso", "desbloque", "regulariz", "confirma")
PALAVRAS_LOJA = ("loja", "outlet", "promo", "desconto", "oferta", "black", "store", "shop", "liquida")
PALAVRAS_FINANCEIRAS = ("pix", "invest", "lucro", "cripto", "crypto", "bet", "cassino", "casino",
                        "saque", "renda", "trade", "wallet", "airdrop", "bonus")

# marca -> domínios oficiais (domínio registrável)
DOMINIOS_OFICIAIS = {
    "itau": ["itau.com.br"], "bradesco": ["bradesco.com.br"], "santander": ["santander.com.br"],
    "nubank": ["nubank.com.br"], "caixa": ["caixa.gov.br"], "bancodobrasil": ["bb.com.br"],
    "picpay": ["picpay.com"], "mercadopago": ["mercadopago.com.br"],
    "mercadolivre": ["mercadolivre.com.br"], "correios": ["correios.com.br"],
    "serasa": ["serasa.com.br", "serasaexperian.com.br"], "netflix": ["netflix.com"],
    "amazon": ["amazon.com.br", "amazon.com"], "apple": ["apple.com"], "icloud": ["icloud.com"],
    "microsoft": ["microsoft.com", "live.com", "office.com"], "outlook": ["outlook.com", "live.com"],
    "google": ["google.com", "google.com.br"], "gmail": ["gmail.com", "google.com"],
    "whatsapp": ["whatsapp.com", "wa.me"], "instagram": ["instagram.com"],
    "facebook": ["facebook.com", "fb.com"], "discord": ["discord.com", "discord.gg", "discordapp.com", "discord.gift"],
    "steam": ["steampowered.com", "steamcommunity.com"], "roblox": ["roblox.com"],
    "shopee": ["shopee.com.br"], "shein": ["shein.com", "shein.com.br"],
    "magalu": ["magazineluiza.com.br", "magalu.com"], "americanas": ["americanas.com.br"],
    "ifood": ["ifood.com.br"], "paypal": ["paypal.com"], "nike": ["nike.com.br", "nike.com"],
    "snapchat": ["snapchat.com"], "netshoes": ["netshoes.com.br"], "casasbahia": ["casasbahia.com.br"],
}
PALAVRAS_DE_GOVERNO = {"gov", "govbr", "receita", "receitafederal", "inss", "meuinss", "detran",
                       "valoresareceber", "fgts", "bolsafamilia", "cnhsocial", "gov-br"}


def _limpar(url: str) -> str:
    return url.rstrip(".,;:!?)]}")


def _dominio_registravel(host: str) -> str:
    host = host.removeprefix("www.")
    partes = host.split(".")
    for sufixo in SUFIXOS_DUPLOS:
        if host.endswith("." + sufixo) or host == sufixo:
            return ".".join(partes[-3:])
    return ".".join(partes[-2:])


def distancia_edicao(a: str, b: str) -> int:
    """Quantas letras precisam mudar para 'a' virar 'b' (distância de Levenshtein)."""
    anterior = list(range(len(b) + 1))
    for i, letra_a in enumerate(a, start=1):
        atual = [i]
        for j, letra_b in enumerate(b, start=1):
            custo = 0 if letra_a == letra_b else 1
            atual.append(min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + custo))
        anterior = atual
    return anterior[-1]


def _normalizar_imitacao(texto: str) -> str:
    """Desfaz truques comuns: rn->m, 0->o, 1->l, vv->w."""
    return (texto.replace("rn", "m").replace("0", "o").replace("1", "l")
            .replace("vv", "w").replace("-", ""))


def analisar_url(url_original: str) -> dict:
    url = _limpar(url_original)
    url_completa = url if re.match(r"^https?://", url, re.IGNORECASE) else "http://" + url
    partes = urlsplit(url_completa)
    netloc = partes.netloc.lower()
    motivos = []
    sinais_bons = []
    marca_imitada = None
    endereco_enganoso = False  # truques para parecer outro site

    if "@" in netloc:
        motivos.append("Tem '@' no endereço: tudo antes do '@' é ignorado pelo navegador.")
        netloc = netloc.split("@")[-1]
        endereco_enganoso = True
    host = netloc.split(":")[0].strip(".")
    dominio = _dominio_registravel(host)
    nome_dominio = dominio.split(".")[0]
    extensao = host.rsplit(".", 1)[-1] if "." in host else ""

    try:
        ipaddress.ip_address(host)
        motivos.append("O endereço é um número de IP, não um nome de site.")
    except ValueError:
        pass

    if host.startswith("xn--") or ".xn--" in host:
        motivos.append("Usa letras de outros alfabetos que imitam letras comuns (punycode).")
        endereco_enganoso = True
    if dominio in ENCURTADORES:
        motivos.append("É um link encurtado: o destino real fica escondido.")
    if extensao in EXTENSOES_SUSPEITAS:
        motivos.append(f"Termina em '.{extensao}', extensão barata muito usada em golpes.")
    hospedagem_generica = None
    for hospedagem in HOSPEDAGEM_GENERICA:
        if host == hospedagem or host.endswith("." + hospedagem):
            hospedagem_generica = hospedagem
            motivos.append(f"Está hospedado em serviço genérico ({hospedagem}); qualquer pessoa pode criar páginas assim.")
            break
    if host.count(".") >= 4:
        motivos.append("Tem muitos subdomínios, um truque para esconder o domínio real.")
    if partes.scheme == "http" and re.match(r"^http://", url, re.IGNORECASE):
        motivos.append("Não usa HTTPS (conexão sem cadeado).")

    caminho = (partes.path or "").lower()
    if caminho.endswith(DOWNLOADS):
        motivos.append("Baixa um arquivo que pode instalar programas no aparelho.")
    consulta = parse_qs(partes.query)
    for chave in ("redirect", "url", "next", "redir", "goto"):
        if any(valor.startswith("http") for valor in consulta.get(chave, [])):
            motivos.append("Redireciona para outro site escondido no fim do link.")
            break

    # Pedaços do endereço: "itau-seguranca.app.xyz" -> ["itau", "seguranca", "app", "xyz"].
    # Em hospedagem genérica, o nome da página fica no caminho (sites.google.com/view/itau-login).
    pedacos = [p for p in re.split(r"[.-]", host) if p]
    if hospedagem_generica:
        pedacos += [p for p in re.split(r"[/._-]", caminho) if p]

    # 1ª passada: o domínio é oficial de alguma marca? (não vale para hospedagem genérica)
    marca_oficial = None
    if not hospedagem_generica:
        for marca, oficiais in DOMINIOS_OFICIAIS.items():
            if dominio in oficiais:
                marca_oficial = marca
                sinais_bons.append(f"Domínio oficial de {marca}.")
                break

    # 2ª passada: se não é oficial, procura imitação de marca
    if marca_oficial is None:
        for marca in DOMINIOS_OFICIAIS:
            usa_nome_da_marca = any(p == marca or p.startswith(marca) for p in pedacos)
            if usa_nome_da_marca:
                marca_imitada = marca
                if hospedagem_generica:
                    motivos.append(f"Usa o nome '{marca}' numa página que qualquer pessoa pode criar em {hospedagem_generica}.")
                else:
                    motivos.append(f"Usa o nome '{marca}', mas o domínio real é '{dominio}', que não é o oficial.")
                break
            imitacao = None
            if len(marca) >= 6:
                # compara o nome do domínio e cada pedaço ("dlscord" em "dlscord-gift.com")
                for pedaco in [nome_dominio] + pedacos:
                    if pedaco != marca and (_normalizar_imitacao(pedaco) == marca or distancia_edicao(pedaco, marca) == 1):
                        imitacao = pedaco
                        break
            if imitacao:
                marca_imitada = marca
                motivos.append(f"O nome '{imitacao}' imita '{marca}' trocando letras.")
                break

    eh_governo = host.endswith(".gov.br") or host == "gov.br"
    if eh_governo:
        sinais_bons.append("Domínio oficial do governo (.gov.br).")
    elif any(p in PALAVRAS_DE_GOVERNO or p.startswith(("govbr", "receita", "inss", "detran")) for p in pedacos):
        motivos.append("Imita um site do governo, mas não termina em .gov.br.")
        marca_imitada = marca_imitada or "governo"

    texto_url = (host + caminho).lower()
    if motivos and caminho.endswith(DOWNLOADS):
        tipo = "download_malicioso"
    elif motivos and (any(p in texto_url for p in PALAVRAS_FINANCEIRAS)):
        tipo = "fraude_financeira"
    elif motivos and (any(p in texto_url for p in PALAVRAS_LOJA) or extensao in ("shop", "store")):
        tipo = "loja_falsa"
    elif motivos and (marca_imitada or endereco_enganoso or any(p in texto_url for p in PALAVRAS_LOGIN)):
        tipo = "roubo_de_dados"
    elif not motivos and sinais_bons:
        tipo = "legitimo_provavel"
    else:
        tipo = "indeterminado"

    return {
        "url": url,
        "dominio_real": dominio,
        "tipo": tipo,
        "suspeito": bool(motivos),
        "imita_marca": bool(marca_imitada) or endereco_enganoso,
        "motivos": motivos,
        "sinais_de_legitimidade": sinais_bons,
    }


def encontrar_links(texto: str) -> list[str]:
    vistos = []
    for encontrado in REGEX_URL.finditer(texto):
        url = _limpar(encontrado.group(0))
        if url and url.lower() not in [v.lower() for v in vistos]:
            vistos.append(url)
    return vistos


def analisar_links(texto: str) -> list[dict]:
    return [analisar_url(url) for url in encontrar_links(texto)]
