"""CRUD dos casos reais que o agente usa para aprender (agente/INTEGRACAO_CRUD.md).

Só a equipe (moderador) cadastra casos, pela página admin.html, rodando no próprio computador.
Os casos ficam num arquivo SQLite (backend/alo_seguro.db, fora do Git).

Regras:
- o texto é SEMPRE anonimizado antes de salvar (CPF, telefone, e-mail, cartão...);
- só táticas que existem em agente/taxonomia.json e golpes que existem na base;
- só casos 'aprovado' e não reservados para teste vão para o prompt da IA (similares.py).
"""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from . import agente, config
from .anonimizar import anonimizar

STATUS = ("pendente", "aprovado", "rejeitado")
ROTULOS = ("golpe", "nao_golpe")
TAMANHO_MINIMO_TEXTO = 3
TAMANHO_MAXIMO_TEXTO = 2000
TAMANHO_MAXIMO_LICAO = 300

ESQUEMA = """
CREATE TABLE IF NOT EXISTS casos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    plataforma           TEXT    NOT NULL,
    texto                TEXT    NOT NULL,
    rotulo               TEXT    NOT NULL CHECK (rotulo IN ('golpe', 'nao_golpe')),
    taticas              TEXT    NOT NULL DEFAULT '[]',
    golpe_base           TEXT,
    licao                TEXT    NOT NULL DEFAULT '',
    status               TEXT    NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovado', 'rejeitado')),
    reservado_para_teste INTEGER NOT NULL DEFAULT 0,
    criado_em            TEXT    NOT NULL,
    atualizado_em        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_casos_status ON casos (status, plataforma);
"""


class CasoInvalido(ValueError):
    """Erro de validação com mensagem para mostrar na tela."""


class CasoNaoEncontrado(LookupError):
    pass


def _agora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(config.CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.executescript(ESQUEMA)
    return conexao


def _para_dict(linha: sqlite3.Row) -> dict:
    caso = dict(linha)
    caso["taticas"] = json.loads(caso["taticas"])
    caso["reservado_para_teste"] = bool(caso["reservado_para_teste"])
    return caso


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def validar(dados: dict, parcial: bool = False) -> tuple[dict, int]:
    """Confere os campos e anonimiza o texto. Devolve (campos_validos, dados_ocultados)."""
    limpo, ocultados = {}, 0

    def tem(campo):
        return campo in dados and dados[campo] is not None

    if tem("plataforma") or not parcial:
        if dados.get("plataforma") not in agente.PLATAFORMAS:
            raise CasoInvalido("Escolha uma plataforma válida.")
        limpo["plataforma"] = dados["plataforma"]

    if tem("texto") or not parcial:
        texto = str(dados.get("texto") or "").strip()
        if len(texto) < TAMANHO_MINIMO_TEXTO:
            raise CasoInvalido("Cole o texto do caso.")
        if len(texto) > TAMANHO_MAXIMO_TEXTO:
            raise CasoInvalido(f"O texto pode ter até {TAMANHO_MAXIMO_TEXTO} caracteres.")
        limpo["texto"], ocultados = anonimizar(texto)

    if tem("rotulo") or not parcial:
        if dados.get("rotulo") not in ROTULOS:
            raise CasoInvalido("Diga se o caso é golpe ou não é golpe.")
        limpo["rotulo"] = dados["rotulo"]

    if tem("taticas") or not parcial:
        taticas = dados.get("taticas") or []
        if not isinstance(taticas, list):
            raise CasoInvalido("Táticas devem ser uma lista.")
        invalidas = [t for t in taticas if t not in agente.taticas_por_id()]
        if invalidas:
            raise CasoInvalido(f"Tática inexistente: {', '.join(map(str, invalidas))}.")
        limpo["taticas"] = json.dumps(list(dict.fromkeys(taticas)), ensure_ascii=False)

    if "golpe_base" in dados or not parcial:
        golpe_base = (dados.get("golpe_base") or "").strip() or None
        if golpe_base and golpe_base not in agente.golpes_por_id():
            raise CasoInvalido(f"O golpe '{golpe_base}' não existe na base.")
        limpo["golpe_base"] = golpe_base

    if tem("licao") or not parcial:
        licao = str(dados.get("licao") or "").strip()
        if len(licao) > TAMANHO_MAXIMO_LICAO:
            raise CasoInvalido(f"A lição pode ter até {TAMANHO_MAXIMO_LICAO} caracteres.")
        limpo["licao"] = licao

    if tem("status") or not parcial:
        status = dados.get("status") or "pendente"
        if status not in STATUS:
            raise CasoInvalido("Status inválido.")
        limpo["status"] = status

    if tem("reservado_para_teste") or not parcial:
        limpo["reservado_para_teste"] = 1 if dados.get("reservado_para_teste") else 0

    return limpo, ocultados


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def criar(dados: dict) -> tuple[dict, int]:
    campos, ocultados = validar(dados)
    campos["criado_em"] = campos["atualizado_em"] = _agora()
    nomes = ", ".join(campos)
    marcas = ", ".join("?" for _ in campos)
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(f"INSERT INTO casos ({nomes}) VALUES ({marcas})", list(campos.values()))
        novo_id = cursor.lastrowid
    return obter(novo_id), ocultados


def obter(caso_id: int) -> dict:
    with closing(conectar()) as conexao:
        linha = conexao.execute("SELECT * FROM casos WHERE id = ?", (caso_id,)).fetchone()
    if linha is None:
        raise CasoNaoEncontrado(caso_id)
    return _para_dict(linha)


def listar(status: str | None = None, plataforma: str | None = None, busca: str | None = None,
           limite: int = 50, deslocamento: int = 0) -> dict:
    condicoes, valores = [], []
    if status:
        condicoes.append("status = ?")
        valores.append(status)
    if plataforma:
        condicoes.append("plataforma = ?")
        valores.append(plataforma)
    if busca:
        condicoes.append("(texto LIKE ? OR licao LIKE ?)")
        valores += [f"%{busca}%", f"%{busca}%"]
    onde = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""
    limite = max(1, min(200, limite))
    with closing(conectar()) as conexao:
        total = conexao.execute(f"SELECT COUNT(*) FROM casos {onde}", valores).fetchone()[0]
        linhas = conexao.execute(f"SELECT * FROM casos {onde} ORDER BY atualizado_em DESC, id DESC LIMIT ? OFFSET ?",
                                 valores + [limite, max(0, deslocamento)]).fetchall()
        por_status = dict(conexao.execute("SELECT status, COUNT(*) FROM casos GROUP BY status").fetchall())
    return {
        "total": total,
        "casos": [_para_dict(linha) for linha in linhas],
        "contagem": {s: por_status.get(s, 0) for s in STATUS},
    }


def atualizar(caso_id: int, dados: dict) -> tuple[dict, int]:
    obter(caso_id)  # 404 se não existir
    campos, ocultados = validar(dados, parcial=True)
    if campos:
        campos["atualizado_em"] = _agora()
        atribuicoes = ", ".join(f"{nome} = ?" for nome in campos)
        with closing(conectar()) as conexao, conexao:
            conexao.execute(f"UPDATE casos SET {atribuicoes} WHERE id = ?", list(campos.values()) + [caso_id])
    return obter(caso_id), ocultados


def excluir(caso_id: int) -> None:
    with closing(conectar()) as conexao, conexao:
        if conexao.execute("DELETE FROM casos WHERE id = ?", (caso_id,)).rowcount == 0:
            raise CasoNaoEncontrado(caso_id)


# ---------------------------------------------------------------------------
# Usado pelo agente (similares.py) e pelo formulário de cadastro
# ---------------------------------------------------------------------------
def casos_aprovados() -> list[dict]:
    """Casos no formato que similares.py espera. Os reservados para teste são filtrados lá."""
    with closing(conectar()) as conexao:
        linhas = conexao.execute("SELECT * FROM casos WHERE status = 'aprovado'").fetchall()
    casos = []
    for linha in linhas:
        caso = _para_dict(linha)
        caso["id"] = f"caso_{caso['id']:04d}"
        casos.append(caso)
    return casos


def sugerir(plataforma: str, texto: str) -> dict:
    """Ajuda o moderador: texto anonimizado + táticas e golpe parecido achados pelas regras (sem IA)."""
    from . import heuristica  # import local: heuristica importa agente, evita ciclo na carga

    if plataforma not in agente.PLATAFORMAS:
        raise CasoInvalido("Escolha uma plataforma válida.")
    texto = (texto or "").strip()
    if len(texto) < TAMANHO_MINIMO_TEXTO:
        raise CasoInvalido("Cole o texto do caso.")
    anonimizado, ocultados = anonimizar(texto[:TAMANHO_MAXIMO_TEXTO])
    regras = heuristica.analisar(plataforma, anonimizado)
    return {
        "texto": anonimizado,
        "dados_ocultados": ocultados,
        "taticas": regras["taticas_detectadas"],
        "golpe_base": regras["golpe_parecido"]["id"] if regras["golpe_parecido"] else None,
        "golpe_base_nome": regras["golpe_parecido"]["nome"] if regras["golpe_parecido"] else None,
        "rotulo_sugerido": "golpe" if regras["probabilidade_golpe"] >= 46 else "nao_golpe",
        "probabilidade_golpe": regras["probabilidade_golpe"],
    }


def opcoes() -> dict:
    """Listas para preencher o formulário da página de moderação."""
    return {
        "plataformas": [{"id": chave, "nome": nome} for chave, nome in agente.PLATAFORMAS.items()],
        "taticas": [{"id": t["id"], "nome": t["nome"], "peso": t["peso"]} for t in agente.taxonomia()["taticas"]],
        "golpes": [{"id": g["id"], "nome": g["nome"]} for g in agente.golpes_por_id().values()],
        "status": list(STATUS),
        "rotulos": list(ROTULOS),
    }
