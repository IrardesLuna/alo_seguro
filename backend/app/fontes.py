"""Fontes de vazamento consultadas pela verificação de exposição (POST /api/v1/check).

Cada fonte é um "adaptador": tem o mesmo jeito de ser chamada, então dá para trocar ou
somar fontes sem mexer nas regras de negócio (README, "Integrações substituíveis").

- FonteDemo: base local de exemplo, não consulta a internet.
- FonteHIBP: Have I Been Pwned (https://haveibeenpwned.com/API/v3), só para e-mail.

Privacidade: nenhuma fonte grava ou registra em log o e-mail ou o telefone consultado.
"""
from dataclasses import dataclass, field
from urllib.parse import quote

import httpx

from . import config


class FonteErro(Exception):
    """Falha ao consultar uma fonte, com mensagem amigável (sem dados pessoais)."""


@dataclass
class Exposicao:
    campo: str                      # "email" ou "telefone"
    fonte: str                      # id da fonte que encontrou
    incidente: str                  # nome do vazamento
    data: str | None                # "AAAA-MM-DD", quando a fonte informa
    dados_expostos: list[str]       # já traduzidos para português
    categorias: set[str] = field(default_factory=set)
    dominio: str | None = None
    verificado: bool = True
    sensivel: bool = False


# Tradução dos tipos de dado usados pelo Have I Been Pwned (e pela base de demonstração)
# e a categoria usada para escolher as recomendações.
TIPOS_DE_DADO = {
    "Email addresses": ("E-mail", "email"),
    "Phone numbers": ("Telefone", "telefone"),
    "Passwords": ("Senha", "senha"),
    "Password hints": ("Dica de senha", "senha"),
    "Security questions and answers": ("Perguntas de segurança", "senha"),
    "Auth tokens": ("Tokens de acesso", "senha"),
    "Credit cards": ("Cartão de crédito", "financeiro"),
    "Partial credit card data": ("Dados parciais de cartão", "financeiro"),
    "Bank account numbers": ("Conta bancária", "financeiro"),
    "Credit status information": ("Situação de crédito", "financeiro"),
    "Income levels": ("Faixa de renda", "financeiro"),
    "Government issued IDs": ("Documento oficial (CPF, RG…)", "documento"),
    "Passport numbers": ("Passaporte", "documento"),
    "National identification numbers": ("Documento oficial (CPF, RG…)", "documento"),
    "Names": ("Nome", "pessoal"),
    "Dates of birth": ("Data de nascimento", "pessoal"),
    "Genders": ("Gênero", "pessoal"),
    "Physical addresses": ("Endereço", "endereco"),
    "Geographic locations": ("Localização", "endereco"),
    "Usernames": ("Nome de usuário", "pessoal"),
    "IP addresses": ("Endereço IP", "tecnico"),
    "Device information": ("Dados do aparelho", "tecnico"),
    "Social media profiles": ("Perfis em redes sociais", "pessoal"),
    "Employers": ("Empregador", "pessoal"),
    "Job titles": ("Cargo", "pessoal"),
    "Private messages": ("Mensagens privadas", "mensagens"),
    "Purchases": ("Histórico de compras", "pessoal"),
}


def traduzir_tipos(tipos: list[str]) -> tuple[list[str], set[str]]:
    nomes, categorias = [], set()
    for tipo in tipos or []:
        nome, categoria = TIPOS_DE_DADO.get(tipo, (tipo, "outros"))
        if nome not in nomes:
            nomes.append(nome)
        categorias.add(categoria)
    return nomes, categorias


def _de_registro_hibp(campo: str, fonte: str, registro: dict) -> Exposicao:
    """Converte um registro no formato do HIBP para uma Exposicao."""
    nomes, categorias = traduzir_tipos(registro.get("DataClasses", []))
    sensivel = bool(registro.get("IsSensitive"))
    return Exposicao(
        campo=campo,
        fonte=fonte,
        # Incidentes sensíveis (ex.: sites adultos) não têm o nome exibido, para não expor a pessoa.
        incidente="Incidente classificado como sensível" if sensivel else str(registro.get("Title") or registro.get("Name") or "Incidente sem nome"),
        data=registro.get("BreachDate"),
        dados_expostos=nomes,
        categorias=categorias,
        dominio=None if sensivel else (registro.get("Domain") or None),
        verificado=bool(registro.get("IsVerified", True)),
        sensivel=sensivel,
    )


class Fonte:
    id = "base"
    nome = "Fonte"
    demonstracao = False
    campos: tuple[str, ...] = ()

    def consultar(self, campo: str, valor: str) -> list[Exposicao]:
        raise NotImplementedError

    def descrever(self) -> dict:
        return {"id": self.id, "nome": self.nome, "demonstracao": self.demonstracao, "campos": list(self.campos)}


class FonteDemo(Fonte):
    """Base local de demonstração, no mesmo formato do HIBP. Dados fictícios."""
    id = "demo"
    nome = "Base de demonstração (dados fictícios)"
    demonstracao = True
    campos = ("email", "telefone")

    REGISTROS = {
        ("email", "teste@exemplo.com"): [
            {"Name": "ColecaoDados2021", "Title": "Coleção de dados \"ColecaoDados2021\" (fictício)",
             "BreachDate": "2021-01-15", "DataClasses": ["Email addresses", "Passwords"], "IsVerified": True},
            {"Name": "LojaExemplo", "Title": "Loja on-line \"LojaExemplo\" (fictícia)", "Domain": "lojaexemplo.com.br",
             "BreachDate": "2023-06-02", "DataClasses": ["Email addresses", "Names", "Phone numbers",
                                                         "Physical addresses", "Partial credit card data"],
             "IsVerified": True},
        ],
        ("telefone", "11999999999"): [
            {"Name": "RedeExemplo", "Title": "Rede social \"RedeExemplo\" (fictícia)", "BreachDate": "2022-08-10",
             "DataClasses": ["Phone numbers", "Names", "Dates of birth", "Government issued IDs"], "IsVerified": True},
        ],
    }

    def consultar(self, campo: str, valor: str) -> list[Exposicao]:
        return [_de_registro_hibp(campo, self.id, r) for r in self.REGISTROS.get((campo, valor), [])]


class FonteHIBP(Fonte):
    """Have I Been Pwned, API v3. A chave fica só no servidor (backend/.env)."""
    id = "hibp"
    nome = "Have I Been Pwned"
    demonstracao = False
    campos = ("email",)
    URL = "https://haveibeenpwned.com/api/v3/breachedaccount/"

    def consultar(self, campo: str, valor: str) -> list[Exposicao]:
        if campo != "email":
            return []
        cabecalhos = {"hibp-api-key": config.HIBP_API_KEY, "user-agent": config.HIBP_USER_AGENT}
        try:
            resposta = httpx.get(self.URL + quote(valor, safe=""), params={"truncateResponse": "false"},
                                 headers=cabecalhos, timeout=config.HIBP_TIMEOUT)
        except httpx.TimeoutException as erro:
            raise FonteErro("A base Have I Been Pwned demorou demais para responder.") from erro
        except httpx.HTTPError as erro:
            raise FonteErro("Não foi possível conectar à base Have I Been Pwned.") from erro

        if resposta.status_code == 404:  # o HIBP responde 404 quando não há vazamentos
            return []
        if resposta.status_code == 401:
            raise FonteErro("A chave do Have I Been Pwned é inválida (confira HIBP_API_KEY no backend/.env).")
        if resposta.status_code == 429:
            raise FonteErro("A base Have I Been Pwned recebeu muitas consultas. Tente de novo em instantes.")
        if resposta.status_code >= 400:
            raise FonteErro(f"A base Have I Been Pwned devolveu um erro ({resposta.status_code}).")
        try:
            registros = resposta.json()
        except ValueError as erro:
            raise FonteErro("A base Have I Been Pwned respondeu num formato inesperado.") from erro
        return [_de_registro_hibp(campo, self.id, r) for r in registros if isinstance(r, dict)]


def fontes_ativas() -> tuple[list[Fonte], str | None]:
    """Fontes configuradas e, se for o caso, um aviso sobre a configuração."""
    if config.FONTE_VAZAMENTOS == "hibp":
        if config.HIBP_API_KEY:
            return [FonteHIBP()], None
        return [FonteDemo()], ("O servidor está configurado para usar o Have I Been Pwned, mas a chave "
                               "não foi informada. Usamos a base de demonstração.")
    return [FonteDemo()], None
