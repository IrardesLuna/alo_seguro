"""Análise por regras (sem IA).

Faz três coisas:
1. procura as táticas de golpe no texto com expressões regulares;
2. calcula a nota com os mesmos pesos e pisos do prompt (seção 7);
3. monta um resultado no mesmo formato da IA, usado quando a IA está indisponível.
"""
import re
import unicodedata

from . import agente
from .links import REGEX_URL, analisar_links

# ---------------------------------------------------------------------------
# 1. Padrões de cada tática (o texto é comparado sem acentos e em minúsculas)
# ---------------------------------------------------------------------------
REGRAS = {
    "pedido_de_codigo": [
        r"(passa|passe|manda|mande|envia|envie|informa|informe|repassa|repasse|me diz|me fala|confirma|confirme|digita|digite)\w*\s+(o |esse |este |aquele |um |seu )?codigo",
        r"codigo (que )?(chegou|recebeu|foi enviado|te mandaram|apareceu)",
        r"(mandei|enviei|mandaram|enviaram) (um |o |uns )?codigo.{0,40}(engano|errado|sem querer)",
        r"codigo de \d ?digitos",
        r"(escane\w+|ler|leia|le) (o |esse |este |um |uma |meu |nosso )?(qr|qrcode|codigo qr)\b",
    ],
    "acesso_remoto": [
        r"\b(anydesk|teamviewer|rustdesk|quicksupport|acesso remoto|airdroid)\b",
        r"compartilh\w+ (a |sua |tua )?tela",
        r"win ?\+ ?r\b|\bctrl ?\+ ?v\b.{0,40}enter",
        r"(cole|colar|cola) (o |este |esse |isso |isto )?(comando|codigo|script)",
        r"conect\w+ (a |sua |tua )?(carteira|wallet)",
        r"instal\w+ (o |um |esse |este |nosso )?(app|aplicativo|programa)\b.{0,40}(seguranca|protecao|suporte|atendimento|banco)",
    ],
    "arquivo_malicioso": [
        r"\b[\w-]+\.(apk|exe|scr|msi|bat|vbs|jar|iso)\b",
        r"habilit\w+ (o |os )?(conteudo|macros?|edicao)",
        r"(baixe|baixar|baixa|instale|instalar) (o |este |esse |a |nova )?(versao|atualizacao|apk|arquivo)",
    ],
    "pagamento_antecipado": [
        r"\btaxa\b.{0,40}(liberar|liberacao|saque|sacar|resgate|receber|entrega|cadastro|inscricao|emissao|desbloque|premio)",
        r"(pague|pagar|paga|deposit\w+|transfir\w+).{0,40}(para|pra) (liberar|sacar|receber|desbloquear|resgatar)",
        r"(so|apenas|somente) (pague|pagar|paga|o valor do) ?(o )?frete",
        r"(pague|pagar|paga) (so|apenas|somente) (o )?(frete|envio|taxa)",
        r"(para|pra) (receber|resgatar|retirar|liberar)\b.{0,40}\b(pague|pagar|paga|deposite|depositar|transfira)",
        r"(compr\w*|adquir\w*|pag\w*) (o |um |seu |nosso )?(kit|pacote|produto|plano)s? (de |da |do )?(boas[- ]vindas|inicial|exclusivo|de entrada|de embaixador)",
        r"\b(frete|taxa|sinal|caucao|imposto)\b.{0,25}(antecipad|antes de (receber|liberar))",
        r"(liberar|desbloquear) (o |seu |sua )?(saque|premio|emprestimo|beneficio|credito)",
    ],
    "recebedor_divergente": [
        r"conta (segura|de seguranca|protegida|transitoria|reserva)",
        r"(esta|fica|ta|vai) (no|em) nome (do|da|de) (meu|minha|um|uma|nosso|nossa)",
        r"(pix|transfer\w+|deposit\w+|paga\w*) (para|pra|na conta d[oa]) (o |a )?(meu|minha) (socio|socia|primo|prima|tio|tia|irmao|irma|amig[oa]|esposa|marido|cunhad[oa]|funcionari[oa])",
        r"(chave|pix) (e |eh )?(o |meu )?cpf",
    ],
    "pedido_de_dinheiro": [
        r"\b(faz|faca|fazer|manda|mande|mandar|envia|envie|transfere|transfira|deposita|deposite)\b.{0,25}\b(pix|deposito|transferencia|ted|valor|dinheiro|grana)\b",
        r"\bpix de\b",
        r"\bme (empresta|emprestar|arruma|ajuda com)\b",
        r"\b(gift ?card|cartao[- ]presente|cartoes[- ]presente|vale[- ]presente)\b",
        r"\b(preciso|precisava|precisando) (de )?(um |uma |uns )?(dinheiro|grana|pix|emprestimo|ajuda financeira)",
        r"\b(pague|pagar) (em|com) (bitcoin|btc|usdt|cripto)",
    ],
    "pedido_de_dados": [
        r"\b(senha|cvv|numero do cartao|dados do cartao|dados bancarios|seed|frase secreta|frase de recuperacao|12 palavras|24 palavras)\b",
        r"(confirm|atualiz|valid|inform|envi|mand|digit|regulariz)\w* (os |seus |os seus |sua |seu )?(dados|cadastro|senha|cpf|documento|rg|cnh)",
        r"\bselfie\b",
        r"foto (do|da|de) (seu |sua )?(rg|cnh|documento|identidade)",
        r"(faca|faz|fazer|efetue) (o )?login|entre (com|na) sua conta",
    ],
    "personificacao_conhecido": [
        r"\b(oi|ola|oie|alo) (mae|mamae|mainha|pai|papai|painho|vo|vovo|tia|tio|filho|filha|amor|mano|mana|irmao|irma|madrinha|padrinho)\b",
        r"\bsou (o|a) (seu|sua|teu|tua) (filho|filha|chefe|gerente|neto|neta|sobrinh[oa]|irmao|irma)",
        r"\b(seu|sua) (chefe|diretor|diretora|gerente) (aqui|falando)",
        r"(nao|n) (me )?reconhece",
        r"\bsou eu[,!. ]",
        r"(denunciei|reportei) (sua|tua) conta",
    ],
    "personificacao_instituicao": [
        r"\b(central de (atendimento|seguranca|relacionamento)|gerente (da sua conta|do banco)|banco central|receita federal|inss|detran|policia (civil|federal|militar)|delegacia|delegado|tribunal|justica|advogad[oa]|escritorio de advocacia|correios|gov\.?br|governo federal|serasa|caixa economica|suporte tecnico|equipe (de )?(suporte|seguranca)|team snapchat|discord (staff|safety|trust)|meta (support|verified)|suporte do (whatsapp|instagram|discord|snapchat))\b",
        r"\b(nubank|itau|bradesco|santander|banco do brasil|mercado (livre|pago)|shopee|amazon|netflix|microsoft|apple|paypal|ifood|picpay)\b",
        r"\bfala com o (staff|suporte|admin|moderador|atendente)\b|\b(staff|admin|moderador)\b.{0,30}\b(discord|servidor|suporte)\b",
        # Como a pessoa descreve o contato: "ligaram do banco", "aqui é da central do cartão", "disse ser do banco".
        r"\b(ligaram|ligou|me ligam|mandaram|mandou|disse\w*|dizendo|falou|falaram|se (diz|disse|apresent\w*)|aqui e|sou|somos)\b"
        r".{0,25}\b(d[oa]|ser d[oa]) (banco|central|cartao|operadora|seguranca do banco)\b",
        r"\b(funcionari[oa]|atendente|gerente)\b.{0,15}\b(d[oa]) (banco|cartao)\b",
    ],
    "troca_de_canal": [
        r"(numero|celular|chip|whats|whatsapp|zap|conta|perfil) nov[oa]",
        r"troquei (de )?(numero|celular|chip|conta)",
        r"salva (esse|este|meu|o|aqui o) (numero|contato)",
        r"(chama|me chama|fala comigo|continua\w*|vamos|me add\w*) (no|pelo|para o|pro|via) (telegram|whatsapp|whats|zap|signal|privado|pv|dm|direct)",
        r"(perdi|quebrou|caiu|roubaram|molhou|estragou) (o |meu )?(celular|telefone|chip|aparelho)",
    ],
    "link_suspeito": [
        r"(clique|clica|clicar|acesse|acessa|acessar|entre|entra) (no|neste|nesse|pelo|o) link",
    ],
    "promessa_irreal": [
        r"(lucro|rendimento|retorno) (garantido|certo|diario|fixo)",
        r"\d+ ?% (ao|por|de lucro ao) (dia|semana)",
        r"(voce|vc|tu) (foi|esta|e o|e a) (sorteado|sorteada|premiado|premiada|selecionado|selecionada|contemplado|contemplada|ganhador|ganhadora)",
        r"(dinheiro|renda|grana) (facil|extra garantida|rapid[oa])",
        r"(multiplic|dobr|tripl)\w+ (seu|o seu|teu|o) (dinheiro|pix|valor|investimento)",
        r"\b(gratis|de graca|gratuito)\b.{0,30}(iphone|celular|pix|premio|nitro|robux|brinde)",
        r"\b(iphone|celular|pix|premio|nitro|robux|v-?bucks|skins?|brinde)s? (gratis|de graca|gratuit[oa]s?)\b",
        r"(ganha|ganhe|ganhar|recebe|receber) comiss",
        r"(desconto|off) de (6|7|8|9)\d ?%|(6|7|8|9)\d ?% (de desconto|off)",
        r"(ganhe|ganha|ganhar|fature|faturar) (r\$ ?\d|ate r\$|\d+ (reais|mil))",
    ],
    "ameaca_medo": [
        r"(sera|vai ser|foi|serao|esta sendo) (bloquead|suspens|cancelad|desativad|encerrad|banid|excluid|removid|negativad)\w*",
        r"(bloqueio|suspensao|cancelamento|desativacao|exclusao) (da|de|do) (sua |seu )?(conta|cpf|cartao|perfil|whatsapp|beneficio)",
        r"(mandado de prisao|ordem de prisao|sera pres[oa]|processo (judicial|criminal)|intimacao|acao judicial)",
        r"(vou|vamos|irei) (mandar|enviar|divulgar|postar|expor|vazar|espalhar|publicar|mostrar)",
        r"(ultimo|ultima) (aviso|notificacao|chance)",
    ],
    "evita_verificacao": [
        r"(nao|n) (posso|consigo|da pra|da para|to podendo|estou podendo) (falar|atender|ligar|fazer (video|chamada)|chamada)",
        r"(microfone|camera|audio|celular) (quebrad|nao (esta |ta )?funcionando|estragad|com defeito)",
        r"(so|apenas|somente) (por )?(mensagem|texto|msg|escrito)",
        r"nao (precisa|tem como|da pra) (ver|visitar|vir buscar|conferir)",
        r"(estou|to|tou) (no trabalho|em reuniao|ocupad[oa]|sem tempo)",
    ],
    "sigilo": [
        r"nao (conta|fala|comenta|diga|conte|fale|comente|mostra|mostre) (pra|para|com|a) (ninguem|seus pais|sua familia|o banco|seu gerente|ninguem)",
        r"\b(confidencial|sigilos[oa]|em segredo|entre nos|so entre a gente)\b",
    ],
    "documento_falso": [
        r"(segue|olha|aqui (esta|ta)|em anexo|anexo|enviei|mandei) (o |a |um |uma )?(comprovante|boleto|intimacao|nota fiscal|apolice|print do (pix|pagamento)|recibo)",
        r"pix (agendado|em processamento|em analise)",
    ],
    "uso_de_ia": [
        r"\b(audio|video|voz)\b.{0,30}\b(da sua|do seu|de sua|de seu) (filh|mae|pai|neto|neta|esposa|marido)",
        r"\b(deepfake|gerad[oa] por ia|inteligencia artificial)\b",
    ],
    "conteudo_intimo": [
        r"\b(nude|nudes|pelad[oa]s?|intim[oa]s?|sexo|sexual|pack|sextape|onlyfans|conteudo adulto|\+18|safadeza)\b",
        r"fotos? (sensua|quente|ousad|sem roupa)",
        r"(chamada|video ?chamada) (de video )?(so |apenas )?(nos dois|a dois|privad)",
        r"(tenho|vi|gravei|tenho aqui) (suas|tuas|as suas) (fotos|imagens)|(tenho|gravei) (seu|teu|o seu) video",
    ],
    "urgencia": [
        r"\b(urgente|urgencia|imediatamente|depressa|correndo|o quanto antes|com pressa)\b",
        r"\b(agora|hoje) (mesmo|ainda)\b|\bate (hoje|amanha|as \d)|\bate (as )?\d{1,2} ?h",
        r"\b(so hoje|apenas hoje|ultim[oa]s? (vagas|horas|unidades|chance|dia))\b",
        r"\b(expira|vence|encerra)\w* (hoje|em \d)",
        r"\bem (\d+|uma|duas) (minutos?|horas?|h)\b|\b(24|48) ?h(oras)?\b",
    ],
    "falta_de_dados": [
        r"\b(prezad[oa]|car[oa]) (cliente|usuario|senhor|senhora|correntista|beneficiario)\b",
        r"(seu|sua) (filho|filha|neto|neta|parente|familiar|marido|esposa) (sofreu|esta|foi|teve|se envolveu|bateu)",
        r"(nao|n) (me )?reconhece",
        r"\bsua (encomenda|entrega)\b|\bseu (pedido|processo|pacote|beneficio) (esta|foi|ficou)",
    ],
    "apelo_emocional": [
        r"\b(pelo amor de deus|desesperad[oa]|chorando|socorro|unica esperanca|morrendo|te amo|meu amor|saudade)\b",
        r"\b(hospital|acidente|uti|cirurgia|internad[oa]|cancer)\b",
        r"(e voce|e vc|essa e voce) (nesse|nessa|neste|nesta) (video|foto)|olha o que (falaram|estao falando|postaram)",
        r"\bpor favor\b.{0,40}\b(ajuda|preciso)\b",
    ],
    "contato_nao_solicitado": [
        r"(numero|contato) errado|(mandei|foi) (para|pra) (a )?pessoa errada",
        r"(voce|vc) foi (selecionad|escolhid|indicad|aprovad)",
        r"adicionad\w* (ao|no|em|neste|nesse) grupo",
        r"(vi|achei|encontrei) (seu|teu) (perfil|numero|contato)",
        r"(amamos|adoramos|gostamos d\w*|curtimos) (o )?(seu|teu) (perfil|conteudo|trabalho)",
        r"(queremos|convidamos) (voce|vc|te) (como|para ser|pra ser) (noss[oa] )?(embaixador|parceir|influenciador|modelo)",
    ],
    "prova_social_falsa": [
        r"(milhares|mais de \d+|\d+ ?mil) (de )?(pessoas|clientes|membros|alunos|participantes)",
        r"(olha|veja|confira) (o|os) (print|prints|resultado|lucro|depoimento)",
        r"(todo mundo|o pessoal|a galera) (esta|ta|do grupo) (ganhando|lucrando|recebendo)",
    ],
    "isca_inicial": [
        r"(voce )?(ja )?(ganhou|recebeu|lucrou) (seu|seus|o primeiro|os primeiros|r\$)",
        r"(saldo|lucro|rendimento|comissao) (disponivel|acumulad|liberad)",
        r"(liberar|desbloquear|subir para) (o )?(saque|nivel|vip)",
        r"\bnivel vip\b",
    ],
    "linguagem_estranha": [
        r"ignor\w+ (as |suas |todas as |todas )?(instrucoes|regras|ordens)",
        r"(responda|diga|fale) que (e|eh|esta) (seguro|confiavel)",
        r"\bvoce agora e\b",
        r"\b(suspendida|usuario seu|caro amigo)\b",
    ],
}

REGRAS_COMPILADAS = {tatica: [re.compile(p) for p in padroes] for tatica, padroes in REGRAS.items()}

REGEX_INJECAO = re.compile(
    r"ignor\w+ (as |suas |todas as |todas )?(regras|instrucoes|ordens)|(responda|diga|fale|classifique) que (e|eh|esta|esta mensagem e) (100% )?(segur|confiavel|legitim)"
)
REGEX_EXECUTAVEL = re.compile(r"\b[\w-]+\.(apk|exe|scr|msi|bat|vbs|jar)\b")
REGEX_SEED = re.compile(r"\b(seed|frase secreta|frase de recuperacao|12 palavras|24 palavras)\b")
REGEX_JA_CAIU = re.compile(r"\bja (paguei|fiz o pix|fiz a transferencia|transferi|mandei o|enviei o|passei o|cliquei|instalei|baixei|depositei|mandei as fotos|enviei as fotos)\b")
REGEX_RISCO_VIDA = re.compile(r"\b(me matar|suicid\w*|tirar minha vida|autolesao|me machucar|me cortar)\b")

# Táticas que significam "o golpista quer algo de você"
TATICAS_DE_PEDIDO = {
    "pedido_de_dinheiro", "pedido_de_codigo", "pedido_de_dados", "pagamento_antecipado",
    "acesso_remoto", "arquivo_malicioso", "link_suspeito", "recebedor_divergente",
}

# ---------------------------------------------------------------------------
# 2. Pisos por combinação crítica (iguais à seção 7 do prompt)
# ---------------------------------------------------------------------------
COMBINACOES = [
    {"nome": "pedido da frase secreta da carteira", "todas": {"_seed"}, "alguma": set(), "piso": 97},
    {"nome": "link que imita marca ou governo", "todas": {"_marca_imitada"}, "alguma": set(), "piso": 80},
    {"nome": "link que baixa arquivo", "todas": {"_download"}, "alguma": set(), "piso": 80},
    {"nome": "link com vários sinais técnicos de fraude", "todas": {"_link_varios_sinais"}, "alguma": set(), "piso": 70},
    {"nome": "tentativa de enganar o detector", "todas": {"_injecao"}, "alguma": set(), "piso": 75},
    {"nome": "pedido de código", "todas": {"pedido_de_codigo"}, "alguma": set(), "piso": 90},
    {"nome": "acesso remoto pedido por instituição", "todas": {"acesso_remoto", "personificacao_instituicao"}, "alguma": set(), "piso": 90},
    {"nome": "sextorsão", "todas": {"conteudo_intimo", "ameaca_medo"}, "alguma": set(), "piso": 90},
    {"nome": "número novo pedindo dinheiro", "todas": {"personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro"}, "alguma": set(), "piso": 88},
    {"nome": "pagamento antecipado", "todas": {"pagamento_antecipado"}, "alguma": set(), "piso": 85},
    {"nome": "arquivo suspeito enviado", "todas": {"arquivo_malicioso"}, "alguma": {"contato_nao_solicitado", "personificacao_instituicao", "personificacao_conhecido"}, "piso": 85},
    {"nome": "instituição falsa com link", "todas": {"personificacao_instituicao", "link_suspeito"}, "alguma": {"pedido_de_dados", "urgencia"}, "piso": 80},
    {"nome": "ameaça com pedido urgente de dinheiro", "todas": {"ameaca_medo", "pedido_de_dinheiro", "urgencia"}, "alguma": set(), "piso": 80},
    {"nome": "promessa de lucro com pedido de dinheiro", "todas": {"promessa_irreal", "pedido_de_dinheiro"}, "alguma": set(), "piso": 80},
    {"nome": "cobrança com recebedor diferente", "todas": {"recebedor_divergente", "personificacao_instituicao"}, "alguma": set(), "piso": 75},
]

POR_QUE = {
    "pedido_de_codigo": "Códigos de verificação dão acesso à sua conta. Ninguém legítimo pede que você repasse.",
    "acesso_remoto": "Com acesso ao aparelho, o golpista pode mexer no seu banco e nas suas contas.",
    "arquivo_malicioso": "Arquivos como .apk e .exe podem instalar programas que roubam dados.",
    "pagamento_antecipado": "Quem vai te pagar não cobra taxa antes. Esse é um dos golpes mais antigos.",
    "recebedor_divergente": "O dinheiro iria para alguém diferente de quem diz estar cobrando.",
    "pedido_de_dinheiro": "Há um pedido de dinheiro: o principal objetivo da maioria dos golpes.",
    "pedido_de_dados": "Pedem dados sensíveis que permitem roubar contas ou abrir crédito no seu nome.",
    "personificacao_conhecido": "Golpistas fingem ser parentes, amigos ou chefes para ganhar sua confiança.",
    "personificacao_instituicao": "Golpistas usam nomes de bancos, governo e empresas para parecer oficiais.",
    "troca_de_canal": "Com número ou canal novo, você não consegue confirmar pelo contato antigo.",
    "link_suspeito": "O link tem sinais de site falso ou esconde o destino real.",
    "promessa_irreal": "Promessas boas demais são a isca mais comum dos golpes.",
    "ameaca_medo": "O medo é usado para você agir rápido, sem pensar.",
    "evita_verificacao": "Quem evita ligação ou vídeo geralmente não quer ser descoberto.",
    "sigilo": "Pedido de segredo serve para impedir que alguém te alerte.",
    "documento_falso": "Comprovantes e documentos enviados como imagem são fáceis de falsificar.",
    "uso_de_ia": "Vozes e vídeos podem ser imitados por inteligência artificial.",
    "conteudo_intimo": "Conteúdo íntimo é muito usado em chantagem (sextorsão).",
    "urgencia": "A pressa impede você de checar a história.",
    "falta_de_dados": "Faltam dados que permitiriam conferir a história (nomes, números, protocolos).",
    "apelo_emocional": "Emoção forte (pena, amor, susto) atrapalha o julgamento.",
    "contato_nao_solicitado": "Alguém que você não conhece puxou conversa ou ofereceu algo.",
    "prova_social_falsa": "Prints e depoimentos são fáceis de inventar.",
    "isca_inicial": "Ganhos pequenos no começo servem para ganhar sua confiança.",
    "linguagem_estranha": "O texto tem trechos estranhos ou tenta manipular o sistema de análise.",
}

# ---------------------------------------------------------------------------
# Dicas de confirmação: como ter certeza de que a mensagem é legítima.
# Escolhidas pelo contexto de quem a mensagem diz ser.
# ---------------------------------------------------------------------------
CONTEXTOS = {
    "familia": re.compile(r"\b(mae|mamae|mainha|pai|papai|painho|filh[oa]|vo|vovo|vovó|neto|neta|tia|tio|irmao|irma|mana|mano|amor|esposa|marido|madrinha|padrinho)\b"),
    "instituicao": re.compile(r"\b(banco|central|suporte|equipe|governo|gov|receita|inss|detran|correios|policia|delegacia|advogad\w*|tribunal|justica|serasa|cartao|conta|empresa|atendimento)\b"),
    "compra": re.compile(r"\b(pix|pagamento|pagar|compra|comprar|venda|vender|produto|entrega|frete|pedido|boleto|loja|preco|valor|r\$)"),
}

DICAS_CONFIRMACAO = {
    "familia": [
        "Confira se a mensagem veio do número que você já tem salvo na agenda, e não de um número novo ou desconhecido.",
        "Ligue para a pessoa no número de sempre ou peça uma chamada de vídeo rápida.",
        "Faça uma pergunta que só vocês sabem, como um apelido de família ou o nome do primeiro bicho de estimação. Evite perguntas cuja resposta esteja nas redes sociais.",
        "Combinem uma palavra-senha da família para usar sempre que alguém pedir dinheiro por mensagem.",
    ],
    "instituicao": [
        "Não responda pelo mesmo canal: abra o app oficial ou digite você mesmo o endereço do site no navegador.",
        "Ligue para o número oficial (o do verso do cartão ou o do site da empresa) e pergunte se o aviso é real.",
        "Confira se o perfil ou o remetente tem selo de verificação e se o nome bate exatamente com o da empresa.",
    ],
    "compra": [
        "Antes de qualquer Pix, confira se o nome do recebedor é o da loja ou da pessoa com quem você negociou.",
        "Pesquise o nome e o CNPJ da loja no Reclame Aqui e prefira pagar dentro da plataforma, com cartão.",
    ],
    "link": [
        "Não faça login nem informe dados pelo link: digite você mesmo o endereço oficial no navegador.",
        "Leia o domínio real do link (o trecho antes da primeira '/') letra por letra.",
    ],
    "email": [
        "Veja o endereço completo do remetente, não só o nome que aparece.",
        "Não abra anexos nem links inesperados; entre no serviço pelo app ou pelo site oficial.",
    ],
    "geral": [
        "Se a pessoa disser quem é, confirme por outro canal que você já conhece (contato salvo, ligação ou site oficial).",
        "Desconfie se, mais tarde, a conversa mudar para pedidos de dinheiro, códigos ou dados.",
        "Na dúvida, mostre a mensagem para alguém de confiança antes de responder.",
    ],
}


def dicas_de_confirmacao(plataforma: str, texto_normalizado: str, tem_links: bool = False) -> list[str]:
    """Dicas para a pessoa ter certeza de que a mensagem é legítima, conforme o contexto."""
    contextos = [nome for nome, padrao in CONTEXTOS.items() if padrao.search(texto_normalizado)]
    if tem_links:
        contextos.append("link")
    if plataforma == "email":
        contextos.append("email")
    contextos.append("geral")

    dicas = []
    for contexto in contextos:
        for dica in DICAS_CONFIRMACAO[contexto]:
            if dica not in dicas:
                dicas.append(dica)
    return dicas


AJUDA = ("CVV 188 (24h, gratuito) · Polícia 190 · Disque 100 (crianças e direitos humanos) · "
         "SaferNet (canal de ajuda e denúncia de crimes na internet)")

SE_JA_CAIU = [
    "Se pagou por Pix: fale agora com o seu banco pelo app ou telefone oficial e peça o MED (Mecanismo Especial de Devolução).",
    "Registre um boletim de ocorrência (pode ser pela delegacia online do seu estado).",
    "Guarde prints da conversa, números, links e comprovantes: são provas.",
    "Se passou código ou senha: recupere a conta pelo app oficial, troque as senhas e ative a verificação em duas etapas.",
    "Avise seus contatos, porque o golpista pode tentar enganá-los usando o seu nome.",
]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, mantendo o mesmo tamanho do texto original."""
    letras = []
    for caractere in texto:
        base = unicodedata.normalize("NFKD", caractere)[0] if caractere else caractere
        letras.append(base.lower()[0])
    return "".join(letras)


def _trecho(original: str, inicio: int, fim: int) -> str:
    inicio = max(0, inicio - 15)
    fim = min(len(original), fim + 20)
    while inicio > 0 and not original[inicio - 1].isspace():
        inicio -= 1
    while fim < len(original) and not original[fim].isspace():
        fim += 1
    trecho = " ".join(original[inicio:fim].split())
    return trecho if len(trecho) <= 120 else trecho[:117] + "..."


def _nivel(nota: int) -> str:
    if nota <= 15:
        return "baixo"
    if nota <= 45:
        return "medio"
    if nota <= 79:
        return "alto"
    return "muito_alto"


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# 3. Detecção e pontuação
# ---------------------------------------------------------------------------
def detectar_taticas(texto: str, links: list[dict]) -> dict:
    """Devolve {tatica: trecho} com a primeira evidência encontrada de cada tática."""
    # Os links têm análise própria: trocamos cada link por espaços (mesmo tamanho)
    # para que "nubank.com.br" não conte como "se passa por instituição".
    sem_links = REGEX_URL.sub(lambda achado: " " * len(achado.group(0)), texto)
    texto_normalizado = normalizar(sem_links)
    encontradas = {}
    for tatica, padroes in REGRAS_COMPILADAS.items():
        for padrao in padroes:
            achado = padrao.search(texto_normalizado)
            if achado:
                encontradas[tatica] = _trecho(texto, achado.start(), achado.end())
                break

    for link in links:
        if link["suspeito"] and "link_suspeito" not in encontradas:
            encontradas["link_suspeito"] = link["url"]
        if link["tipo"] == "download_malicioso" and "arquivo_malicioso" not in encontradas:
            encontradas["arquivo_malicioso"] = link["url"]
        if link["imita_marca"] and "personificacao_instituicao" not in encontradas:
            encontradas["personificacao_instituicao"] = link["url"]
    return encontradas


def sinais_dos_links(links: list[dict]) -> set:
    """Sinais técnicos fortes vindos da análise de links (usados nos pisos)."""
    sinais = set()
    for link in links:
        if link["imita_marca"]:
            sinais.add("_marca_imitada")
        if link["tipo"] == "download_malicioso":
            sinais.add("_download")
        if len(link["motivos"]) >= 2:
            sinais.add("_link_varios_sinais")
    return sinais


def calcular_nota(taticas: set, extras: set | None = None) -> dict:
    """Soma os pesos, aplica pisos e limites. 'extras' são sinais especiais (ex.: '_seed')."""
    pesos = agente.taticas_por_id()
    soma = 3
    for tatica in taticas:
        soma += pesos[tatica]["pontos"]

    presentes = set(taticas) | (extras or set())
    pisos_aplicados = []
    for combinacao in COMBINACOES:
        tem_todas = combinacao["todas"] <= presentes
        tem_alguma = not combinacao["alguma"] or bool(combinacao["alguma"] & presentes)
        if tem_todas and tem_alguma:
            pisos_aplicados.append(combinacao)

    nota = soma
    if pisos_aplicados:
        nota = max(nota, max(c["piso"] for c in pisos_aplicados))
        if len(pisos_aplicados) >= 2:
            nota += 5  # reforço por várias combinações críticas

    tem_pedido = bool(presentes & TATICAS_DE_PEDIDO) or any(p.startswith("_") for p in presentes)
    tem_forte = any(pesos[t]["peso"] == "forte" for t in taticas)
    if not tem_pedido and not tem_forte:
        nota = min(nota, 25)  # sem pedido, ainda não é golpe

    nota = max(1, min(99, nota))  # nunca 0% e nunca 100%
    return {"nota": nota, "soma": soma, "pisos": [c["nome"] for c in pisos_aplicados]}


# Marcas que aparecem nos nomes de golpes da base. Um golpe "da PayPal" só pode ser o mais
# parecido se a mensagem falar da PayPal.
MARCAS_NOS_NOMES = (
    "paypal", "netflix", "apple", "icloud", "google", "microsoft", "linkedin", "zoom", "teams",
    "meta", "nubank", "itau", "bradesco", "santander", "caixa", "steam", "roblox", "riot", "epic",
    "nitro", "hypesquad", "shopee", "shein", "mercado livre", "olx", "correios", "inss", "detran",
    "receita", "serasa", "fgts", "enem", "fies", "prouni", "bolsa familia", "ifood", "iphone",
    "tigrinho", "valorant", "snapchat+", "spotlight", "airbnb", "booking", "gov.br", "ipva",
    "iptu", "inpi", "spc",
)


def _marca_incompativel(nome_golpe: str, texto_normalizado: str) -> bool:
    nome = normalizar(nome_golpe)
    for marca in MARCAS_NOS_NOMES:
        if marca in nome and marca not in texto_normalizado:
            return True
    return False


def radicais(texto_normalizado: str) -> set:
    """Começo (5 letras) das palavras com 4+ letras: 'bloqueada' e 'bloqueio' viram 'bloqu'."""
    return {palavra[:5] for palavra in re.findall(r"[a-z]{4,}", texto_normalizado)}


def golpe_mais_parecido(plataforma: str, taticas: set, texto_normalizado: str = "") -> dict | None:
    """Compara táticas (60%) e palavras (40%) com cada golpe da base."""
    if len(taticas) < 2:
        return None
    radicais_mensagem = radicais(texto_normalizado)
    melhor, melhor_nota = None, 0.0
    for golpe in agente.base_golpes(plataforma):
        if _marca_incompativel(golpe["nome"], texto_normalizado):
            continue  # ex.: não chamar um e-mail do Itaú de "PayPal falso"
        texto_golpe = normalizar(" ".join([golpe["nome"], golpe["resumo"], *golpe["sinais"]]))
        em_comum = len(radicais_mensagem & radicais(texto_golpe))
        if em_comum == 0:
            continue  # nenhuma palavra em comum: não é o mesmo golpe
        nota = 0.6 * jaccard(taticas, set(golpe["taticas"])) + 0.4 * min(1.0, em_comum / 3)
        if nota > melhor_nota:
            melhor, melhor_nota = golpe, nota
    if melhor is None or melhor_nota < 0.5:
        return None
    return {"id": melhor["id"], "nome": melhor["nome"], "similaridade": round(melhor_nota * 100)}


def analisar(plataforma: str, texto: str) -> dict:
    """Análise completa por regras, no mesmo formato da resposta da IA."""
    links = analisar_links(texto)
    evidencias = detectar_taticas(texto, links)
    taticas = set(evidencias)
    texto_normalizado = normalizar(texto)
    extras = sinais_dos_links(links)
    if REGEX_SEED.search(texto_normalizado):
        extras.add("_seed")
    if REGEX_EXECUTAVEL.search(texto_normalizado):
        extras.add("_download")  # arquivo de instalação enviado na conversa
    if REGEX_INJECAO.search(texto_normalizado):
        extras.add("_injecao")   # mensagem tentando enganar o próprio detector
    calculo = calcular_nota(taticas, extras)
    nota = calculo["nota"]
    nivel = _nivel(nota)
    pesos = agente.taticas_por_id()

    ordenadas = sorted(taticas, key=lambda t: pesos[t]["pontos"], reverse=True)
    red_flags = [
        {"trecho": evidencias[t], "tatica": t, "explicacao": POR_QUE[t]}
        for t in ordenadas[:6]
    ]

    parecido = golpe_mais_parecido(plataforma, taticas, texto_normalizado)
    # Dicas: 1) a do golpe parecido, 2) como confirmar quem enviou, 3) as das táticas encontradas.
    confirmacao = dicas_de_confirmacao(plataforma, texto_normalizado, bool(links))
    candidatas = []
    if parecido:
        candidatas.append(agente.golpes_por_id()[parecido["id"]]["dicas"][0])
    candidatas += confirmacao[:3]
    candidatas += [pesos[t]["dica_padrao"] for t in ordenadas]
    candidatas += confirmacao[3:]
    dicas = []
    for dica in candidatas:
        if dica not in dicas:
            dicas.append(dica)
        if len(dicas) >= 5:
            break

    vereditos = {
        "baixo": "Não encontramos sinais fortes de golpe.",
        "medio": "Há alguns sinais de alerta. Confirme antes de agir.",
        "alto": "Esta mensagem tem vários sinais de golpe.",
        "muito_alto": "Muito provavelmente é golpe.",
    }
    veredito = vereditos[nivel]
    if parecido and nivel in ("alto", "muito_alto"):
        veredito += f" Parece o \"{parecido['nome']}\"."
    if not taticas and links and all(l["tipo"] == "legitimo_provavel" for l in links):
        veredito = "O link parece ser do site oficial."

    if taticas:
        nomes = ", ".join(pesos[t]["nome"].lower() for t in ordenadas[:4])
        explicacao = f"As regras automáticas encontraram: {nomes}."
    else:
        explicacao = "As regras automáticas não encontraram padrões conhecidos de golpe nesta mensagem."
    if calculo["pisos"]:
        explicacao += f" A combinação \"{calculo['pisos'][0]}\" é típica de golpe."

    risco_vida = bool(REGEX_RISCO_VIDA.search(texto_normalizado))
    precisa_ajuda = risco_vida or "conteudo_intimo" in taticas
    ja_caiu = bool(REGEX_JA_CAIU.search(texto_normalizado))

    return {
        "probabilidade_golpe": nota,
        "nivel": nivel,
        "confianca_analise": "media" if len(taticas) >= 3 else "baixa",
        "veredito": veredito,
        "explicacao": explicacao,
        "canal_analisado": plataforma,
        "golpe_parecido": parecido,
        "taticas_detectadas": ordenadas,
        "red_flags": red_flags,
        "sinais_de_legitimidade": [s for link in links for s in link["sinais_de_legitimidade"]],
        "dicas": dicas,
        "se_ja_caiu": SE_JA_CAIU if ja_caiu else [],
        "analise_link": [
            {"url": l["url"], "dominio_real": l["dominio_real"], "tipo": l["tipo"], "motivos": l["motivos"]}
            for l in links
        ],
        "aviso_ajuda": AJUDA if precisa_ajuda else None,
        "possivel_golpe_novo": False,
        "observacoes": None,
        "_calculo": calculo,
        "_evidencias": evidencias,
        "_links": links,
    }
