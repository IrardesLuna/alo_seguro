"""Verificação de exposição em vazamentos (POST /api/v1/check).

Fluxo:
1. valida e normaliza e-mail e telefone;
2. consulta as fontes ativas (fontes.py) só para os campos que cada uma cobre;
3. escolhe recomendações de um catálogo fixo, conforme os tipos de dado expostos;
4. se a IA estiver ligada, o agente (agente/prompt_vazamento.md) escreve o resumo e ordena as
   recomendações. A IA recebe só metadados: nunca o e-mail ou o telefone.

Nada do que a pessoa informa é guardado ou registrado em log.
"""
import re
from datetime import datetime, timezone

from . import agente, config, gemini
from .fontes import Exposicao, FonteErro, fontes_ativas

REGEX_EMAIL = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$")
MESES = ("jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez.")
NOMES_CAMPOS = {"email": "e-mail", "telefone": "telefone"}

AVISO_LIMITES = ("Uma consulta sem correspondências não comprova que seus dados nunca foram expostos: "
                 "o resultado depende das fontes consultadas e de quando elas foram atualizadas.")


class EntradaInvalida(ValueError):
    """Erro de validação com mensagem para mostrar na tela."""


# ---------------------------------------------------------------------------
# Catálogo de recomendações. Textos e links revisados pela equipe: a IA só escolhe e ordena.
# ---------------------------------------------------------------------------
LINK_ANALISAR = {"texto": "Analisar uma mensagem suspeita no Alô Seguro", "url": "#analisar"}
RECOMENDACOES = {
    "contatar_banco": {
        "titulo": "Fale com o seu banco",
        "texto": "Dados de cartão ou de conta apareceram no vazamento. Fale com o banco pelo app ou pelo "
                 "telefone do verso do cartão, peça o bloqueio ou a troca do cartão e acompanhe o extrato.",
        "link": None,
    },
    "trocar_senhas": {
        "titulo": "Troque suas senhas",
        "texto": "Troque a senha do serviço afetado e de todos os sites onde você usa a mesma senha "
                 "ou uma parecida. Comece pelo e-mail e pelo banco.",
        "link": None,
    },
    "conferir_cpf": {
        "titulo": "Confira se usaram seu CPF",
        "texto": "Documentos apareceram no vazamento. No Registrato, do Banco Central, você vê de graça "
                 "contas, empréstimos e chaves Pix registrados no seu CPF.",
        "link": {"texto": "Registrato (Banco Central)", "url": "https://www.bcb.gov.br/cidadaniafinanceira/registrato"},
    },
    "ativar_2fa": {
        "titulo": "Ative a verificação em duas etapas",
        "texto": "Com a verificação em duas etapas (2FA), mesmo quem souber sua senha não entra na conta "
                 "sem um segundo código. Ative no e-mail, no WhatsApp e nas redes sociais.",
        "link": None,
    },
    "golpes_telefone": {
        "titulo": "Fique atento a golpes por telefone e WhatsApp",
        "texto": "Com seu telefone (e às vezes seu nome), golpistas fingem ser banco, loja ou parente. "
                 "Ative a confirmação em duas etapas do WhatsApp e nunca passe códigos recebidos por SMS.",
        "link": LINK_ANALISAR,
    },
    "golpes_email": {
        "titulo": "Desconfie de e-mails sobre o vazamento",
        "texto": "Golpistas mandam e-mails falsos citando vazamentos para pedir que você \"confirme seus "
                 "dados\". Não clique: entre no site digitando o endereço oficial.",
        "link": LINK_ANALISAR,
    },
    "dados_pessoais": {
        "titulo": "Cuidado com quem já sabe seus dados",
        "texto": "Nome, data de nascimento ou endereço ajudam golpistas a parecer confiáveis. Saber seus "
                 "dados não prova que a pessoa é de uma empresa: confirme pelo canal oficial.",
        "link": None,
    },
    "gerenciador_senhas": {
        "titulo": "Use senhas únicas",
        "texto": "Use uma senha longa e diferente para cada site. Um gerenciador de senhas ajuda a "
                 "lembrar de todas.",
        "link": None,
    },
    "boletim_ocorrencia": {
        "titulo": "Se seus dados forem usados em fraude, registre ocorrência",
        "texto": "Se perceber compras, contas ou empréstimos que você não fez, registre um boletim de "
                 "ocorrência (muitos estados têm delegacia on-line) e avise o banco.",
        "link": None,
    },
    "direitos_lgpd": {
        "titulo": "Conheça seus direitos (LGPD)",
        "texto": "Se o vazamento foi de uma empresa que atua no Brasil, você pode pedir a ela explicações "
                 "sobre seus dados. Sem resposta, é possível fazer uma petição à ANPD.",
        "link": {"texto": "Autoridade Nacional de Proteção de Dados (ANPD)", "url": "https://www.gov.br/anpd/pt-br"},
    },
    # Cuidados para quando nada foi encontrado.
    "verificar_periodicamente": {
        "titulo": "Verifique de tempos em tempos",
        "texto": "Novos vazamentos aparecem todo mês. Vale repetir a verificação de vez em quando.",
        "link": None,
    },
    "nunca_dados_bancarios": {
        "titulo": "Nunca informe cartão ou senha para \"verificar\" vazamento",
        "texto": "Nenhum serviço legítimo de verificação pede número de cartão, senha ou dados bancários.",
        "link": None,
    },
}

ORDEM_PADRAO = list(RECOMENDACOES)  # a ordem do catálogo já segue a prioridade
DICAS_SEM_EXPOSICAO = ["gerenciador_senhas", "ativar_2fa", "golpes_email", "verificar_periodicamente",
                       "nunca_dados_bancarios"]


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def normalizar_email(valor: str | None) -> str | None:
    if valor is None or not valor.strip():
        return None
    email = valor.strip().lower()
    if len(email) > 254 or not REGEX_EMAIL.match(email):
        raise EntradaInvalida("Informe um e-mail válido.")
    return email


def normalizar_telefone(valor: str | None) -> str | None:
    """Aceita (11) 91234-5678, +55 11 91234-5678 etc. Devolve DDD + número, só dígitos."""
    if valor is None or not valor.strip():
        return None
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) in (12, 13) and digitos.startswith("55"):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11) or digitos[0] == "0" or digitos[1] == "0":
        raise EntradaInvalida("Informe um telefone válido, com DDD.")
    if len(digitos) == 11 and digitos[2] != "9":
        raise EntradaInvalida("Informe um telefone válido, com DDD.")
    return digitos


def formatar_data(data: str | None) -> str | None:
    """'2021-01-15' -> 'jan. 2021'."""
    try:
        quando = datetime.strptime(data or "", "%Y-%m-%d")
    except ValueError:
        return None
    return f"{MESES[quando.month - 1]} {quando.year}"


# ---------------------------------------------------------------------------
# Recomendações e resumo por regras
# ---------------------------------------------------------------------------
def recomendacoes_por_regras(exposicoes: list[Exposicao]) -> list[str]:
    if not exposicoes:
        return list(DICAS_SEM_EXPOSICAO)
    categorias = set().union(*(e.categorias for e in exposicoes))
    campos = {e.campo for e in exposicoes}
    escolhidas = {"ativar_2fa", "direitos_lgpd"}
    if "financeiro" in categorias:
        escolhidas |= {"contatar_banco", "boletim_ocorrencia"}
    if "senha" in categorias:
        escolhidas |= {"trocar_senhas", "gerenciador_senhas"}
    if "documento" in categorias:
        escolhidas |= {"conferir_cpf", "boletim_ocorrencia"}
    if "telefone" in categorias or "telefone" in campos:
        escolhidas.add("golpes_telefone")
    if "email" in categorias or "email" in campos:
        escolhidas.add("golpes_email")
    if categorias & {"pessoal", "endereco", "documento"}:
        escolhidas.add("dados_pessoais")
    return [id_ for id_ in ORDEM_PADRAO if id_ in escolhidas]


def _juntar(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def resumo_por_regras(status: str, exposicoes: list[Exposicao], nao_verificados: list[str]) -> str:
    faltou = ""
    if nao_verificados:
        faltou = (f" Não conseguimos verificar o {_juntar([NOMES_CAMPOS[c] for c in nao_verificados])} "
                  "nas fontes disponíveis agora.")
    if status == "nao_verificado":
        return "Não foi possível concluir a verificação nas fontes disponíveis." + faltou
    if status == "nada_encontrado":
        return ("Não encontramos seus dados nos vazamentos conhecidos pelas fontes consultadas. "
                "Isso não garante que eles nunca foram expostos." + faltou)
    categorias = set().union(*(e.categorias for e in exposicoes))
    risco = "Golpistas podem usar esses dados para parecer confiáveis em mensagens e ligações."
    if "financeiro" in categorias:
        risco = "Como apareceram dados de cartão ou conta, o mais urgente é falar com o seu banco."
    elif "senha" in categorias:
        risco = "Como apareceu senha, alguém pode tentar entrar nas suas contas: troque-a o quanto antes."
    elif "documento" in categorias:
        risco = "Como apareceram documentos, vale conferir se alguém abriu contas ou empréstimos no seu nome."
    quantidade = len(exposicoes)
    texto = f"Encontramos {quantidade} {'exposição' if quantidade == 1 else 'exposições'} em vazamentos conhecidos. "
    return texto + risco + faltou


# ---------------------------------------------------------------------------
# Agente (IA)
# ---------------------------------------------------------------------------
def _contexto_para_ia(status, exposicoes, verificados, nao_verificados, sugeridas) -> dict:
    """Só metadados: nenhum e-mail, telefone ou domínio de incidente sensível."""
    return {
        "status": status,
        "incidentes": [{"campo": e.campo, "incidente": e.incidente, "data": e.data or "",
                        "dados_expostos": e.dados_expostos, "sensivel": e.sensivel} for e in exposicoes],
        "campos_verificados": verificados,
        "campos_nao_verificados": nao_verificados,
        "recomendacoes_sugeridas": sugeridas,
    }


def _personalizar_com_ia(contexto: dict, sugeridas: list[str]) -> tuple[str, list[str], dict[str, str]]:
    catalogo = {id_: r["titulo"] for id_, r in RECOMENDACOES.items()}
    bruto = gemini.gerar_json(agente.montar_prompt_vazamento(catalogo), agente.montar_mensagem_vazamento(contexto),
                              agente.ESQUEMA_VAZAMENTO, tempo_maximo=20)
    resumo = str(bruto.get("resumo") or "").strip()[:700]
    if not resumo:
        raise gemini.GeminiErro("A IA não devolveu o resumo.")

    ordem = []
    for id_ in bruto.get("ordem_recomendacoes") or []:
        if id_ in RECOMENDACOES and id_ not in ordem:  # ignora ids inventados
            ordem.append(id_)
    ordem += [id_ for id_ in sugeridas if id_ not in ordem]  # as das regras nunca somem

    explicacoes = {}
    for item in bruto.get("explicacoes") or []:
        if isinstance(item, dict) and item.get("id") in ordem and str(item.get("por_que") or "").strip():
            explicacoes[item["id"]] = str(item["por_que"]).strip()[:280]
    return resumo, ordem[:8], explicacoes


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
def consultar(email: str | None, telefone: str | None) -> dict:
    email = normalizar_email(email)
    telefone = normalizar_telefone(telefone)
    pedidos = {campo: valor for campo, valor in (("email", email), ("telefone", telefone)) if valor}
    if not pedidos:
        raise EntradaInvalida("Informe um e-mail ou um telefone para verificar.")

    fontes, aviso_config = fontes_ativas()
    avisos = [aviso_config] if aviso_config else []
    exposicoes: list[Exposicao] = []
    verificados, nao_verificados = [], []
    fontes_usadas = []
    houve_falha = False

    for campo, valor in pedidos.items():
        cobrem = [f for f in fontes if campo in f.campos]
        sucesso = False
        for fonte in cobrem:
            try:
                exposicoes += fonte.consultar(campo, valor)
                sucesso = True
                if fonte.descrever() not in fontes_usadas:
                    fontes_usadas.append(fonte.descrever())
            except FonteErro as erro:
                houve_falha = True
                avisos.append(str(erro))
        if sucesso:
            verificados.append(campo)
        else:
            nao_verificados.append(campo)
            if not cobrem:
                avisos.append(f"Nenhuma fonte configurada consegue verificar {NOMES_CAMPOS[campo]} no momento.")

    if exposicoes:
        status = "exposto"
    elif verificados:
        status = "nada_encontrado"
    else:
        status = "nao_verificado"

    exposicoes.sort(key=lambda e: e.data or "", reverse=True)  # mais recentes primeiro
    sugeridas = recomendacoes_por_regras(exposicoes)
    resumo, ordem, explicacoes, origem = resumo_por_regras(status, exposicoes, nao_verificados), sugeridas, {}, "regras"

    if status == "exposto" and config.IA_NO_VAZAMENTO and gemini.configurado():
        try:
            contexto = _contexto_para_ia(status, exposicoes, verificados, nao_verificados, sugeridas)
            resumo, ordem, explicacoes = _personalizar_com_ia(contexto, sugeridas)
            origem = "ia"
        except gemini.GeminiErro:
            pass  # segue com o resumo e a ordem das regras, sem atrapalhar a pessoa

    return {
        "status": status,
        "resumo": resumo,
        "origem_resumo": origem,
        "campos_verificados": verificados,
        "campos_nao_verificados": nao_verificados,
        "exposicoes": [{
            "campo": e.campo,
            "incidente": e.incidente,
            "dominio": e.dominio,
            "data": e.data,
            "data_formatada": formatar_data(e.data),
            "dados_expostos": e.dados_expostos,
            "verificado": e.verificado,
            "sensivel": e.sensivel,
        } for e in exposicoes],
        "recomendacoes": [dict(RECOMENDACOES[id_], id=id_, por_que=explicacoes.get(id_)) for id_ in ordem],
        "fontes": fontes_usadas,
        "demonstracao": any(f["demonstracao"] for f in fontes_usadas) or (not fontes_usadas and any(f.demonstracao for f in fontes)),
        "avisos": avisos,
        "falha_fonte": houve_falha,
        "aviso_limites": AVISO_LIMITES,
        "consultado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def estado_das_fontes() -> dict:
    fontes, aviso = fontes_ativas()
    return {
        "fontes": [f.descrever() for f in fontes],
        "demonstracao": any(f.demonstracao for f in fontes),
        "aviso": aviso,
    }
