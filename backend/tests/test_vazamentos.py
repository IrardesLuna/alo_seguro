"""Testes da verificação de vazamentos (POST /api/v1/check), sem internet e sem gastar cota da IA."""
import pytest
from fastapi.testclient import TestClient

from app import config, fontes, gemini, main, vazamentos

cliente = TestClient(main.app)


@pytest.fixture(autouse=True)
def ambiente_padrao(monkeypatch):
    main._pedidos_por_ip.clear()
    monkeypatch.setattr(config, "FONTE_VAZAMENTOS", "demo")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")


def checar(**corpo):
    return cliente.post("/api/v1/check", json=corpo)


def test_health():
    dados = cliente.get("/health").json()
    assert dados["status"] == "ok"
    assert dados["vazamentos"]["demonstracao"] is True


def test_email_exposto_na_demo():
    dados = checar(email="  Teste@Exemplo.com ").json()
    assert dados["status"] == "exposto"
    assert dados["demonstracao"] is True
    assert len(dados["exposicoes"]) == 2
    assert dados["exposicoes"][0]["data_formatada"] == "jun. 2023"  # mais recente primeiro
    ids = [r["id"] for r in dados["recomendacoes"]]
    assert ids[0] == "contatar_banco"  # dado de cartão vem antes de tudo
    assert "trocar_senhas" in ids and "golpes_email" in ids
    assert "Senha" in dados["exposicoes"][1]["dados_expostos"]


def test_telefone_com_55_e_documento():
    dados = checar(telefone="+55 (11) 99999-9999").json()
    assert dados["status"] == "exposto"
    ids = [r["id"] for r in dados["recomendacoes"]]
    assert "conferir_cpf" in ids and "golpes_telefone" in ids
    registrato = next(r for r in dados["recomendacoes"] if r["id"] == "conferir_cpf")
    assert registrato["link"]["url"].startswith("https://www.bcb.gov.br/")


def test_nada_encontrado_tem_aviso_de_limites():
    dados = checar(email="ninguem@exemplo.com", telefone="(81) 91234-5678").json()
    assert dados["status"] == "nada_encontrado"
    assert dados["exposicoes"] == []
    assert dados["campos_verificados"] == ["email", "telefone"]
    assert "não comprova" in dados["aviso_limites"]
    assert [r["id"] for r in dados["recomendacoes"]] == vazamentos.DICAS_SEM_EXPOSICAO


def test_resposta_nao_devolve_o_dado_consultado():
    texto = checar(email="teste@exemplo.com", telefone="11999999999").text
    assert "teste@exemplo.com" not in texto and "11999999999" not in texto


@pytest.mark.parametrize("corpo, status", [
    ({}, 422),
    ({"email": "", "telefone": "  "}, 422),
    ({"email": "sem-arroba"}, 422),
    ({"telefone": "1234"}, 422),
    ({"telefone": "(11) 81234-5678"}, 422),  # celular com 11 dígitos começa com 9
    ({"email": "a" * 300 + "@x.com"}, 422),
])
def test_entradas_invalidas(corpo, status):
    assert checar(**corpo).status_code == status


def test_limite_por_minuto(monkeypatch):
    monkeypatch.setattr(config, "LIMITE_POR_MINUTO", 2)
    assert checar(email="a@b.com").status_code == 200
    assert checar(email="c@d.com").status_code == 200
    assert checar(email="e@f.com").status_code == 429


# ----------------------------- Have I Been Pwned -----------------------------
class RespostaFalsa:
    def __init__(self, status, dados=None):
        self.status_code, self._dados = status, dados

    def json(self):
        return self._dados


@pytest.fixture
def hibp(monkeypatch):
    monkeypatch.setattr(config, "FONTE_VAZAMENTOS", "hibp")
    monkeypatch.setattr(config, "HIBP_API_KEY", "chave-de-teste")
    chamadas = []

    def configurar(resposta):
        def get_falso(url, **kwargs):
            chamadas.append((url, kwargs))
            if isinstance(resposta, Exception):
                raise resposta
            return resposta
        monkeypatch.setattr(fontes.httpx, "get", get_falso)
        return chamadas
    return configurar


def test_hibp_traduz_e_esconde_incidente_sensivel(hibp):
    chamadas = hibp(RespostaFalsa(200, [
        {"Name": "Adobe", "Title": "Adobe", "Domain": "adobe.com", "BreachDate": "2013-10-04",
         "DataClasses": ["Email addresses", "Passwords", "Password hints"], "IsVerified": True},
        {"Name": "SiteX", "Title": "SiteX", "Domain": "sitex.com", "BreachDate": "2016-01-01",
         "DataClasses": ["Email addresses"], "IsSensitive": True},
    ]))
    dados = checar(email="maria+teste@exemplo.com").json()
    url, kwargs = chamadas[0]
    assert url.endswith("maria%2Bteste%40exemplo.com")
    assert kwargs["headers"]["hibp-api-key"] == "chave-de-teste"
    assert dados["demonstracao"] is False
    adobe = next(e for e in dados["exposicoes"] if e["dominio"] == "adobe.com")
    assert adobe["dados_expostos"] == ["E-mail", "Senha", "Dica de senha"]
    sensivel = next(e for e in dados["exposicoes"] if e["sensivel"])
    assert "SiteX" not in sensivel["incidente"] and sensivel["dominio"] is None


def test_hibp_404_e_nada_encontrado(hibp):
    hibp(RespostaFalsa(404))
    assert checar(email="limpo@exemplo.com").json()["status"] == "nada_encontrado"


def test_hibp_nao_cobre_telefone(hibp):
    hibp(RespostaFalsa(404))
    dados = checar(email="limpo@exemplo.com", telefone="11912345678").json()
    assert dados["campos_nao_verificados"] == ["telefone"]
    assert "telefone" in dados["resumo"]


def test_hibp_fora_do_ar_responde_503(hibp):
    hibp(fontes.httpx.ConnectTimeout("lento"))
    resposta = checar(email="x@exemplo.com")
    assert resposta.status_code == 503
    assert "demorou" in resposta.json()["detail"]


def test_hibp_sem_chave_usa_demo(monkeypatch):
    monkeypatch.setattr(config, "FONTE_VAZAMENTOS", "hibp")
    monkeypatch.setattr(config, "HIBP_API_KEY", "")
    dados = checar(email="teste@exemplo.com").json()
    assert dados["demonstracao"] is True and dados["avisos"]


# ----------------------------- Agente (IA) -----------------------------
def test_ia_recebe_so_metadados_e_nao_inventa_recomendacoes(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "chave-de-teste")
    recebido = {}

    def ia_falsa(prompt, mensagem, esquema=None, tempo_maximo=None):
        recebido["prompt"], recebido["mensagem"] = prompt, mensagem
        return {"resumo": "Seu e-mail apareceu em dois vazamentos.",
                "ordem_recomendacoes": ["trocar_senhas", "recomendacao_inventada", "contatar_banco"],
                "explicacoes": [{"id": "trocar_senhas", "por_que": "Sua senha apareceu."},
                                {"id": "recomendacao_inventada", "por_que": "x"}]}

    monkeypatch.setattr(gemini, "gerar_json", ia_falsa)
    dados = checar(email="teste@exemplo.com", telefone="11999999999").json()
    assert "teste@exemplo.com" not in recebido["mensagem"] and "11999999999" not in recebido["mensagem"]
    assert "{{" not in recebido["prompt"] and "trocar_senhas:" in recebido["prompt"]
    assert dados["origem_resumo"] == "ia"
    ids = [r["id"] for r in dados["recomendacoes"]]
    assert ids[:2] == ["trocar_senhas", "contatar_banco"]
    assert "recomendacao_inventada" not in ids
    assert "conferir_cpf" in ids  # sugerida pelas regras, não pode sumir
    assert dados["recomendacoes"][0]["por_que"] == "Sua senha apareceu."


def test_ia_com_erro_usa_regras(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "chave-de-teste")

    def ia_quebrada(*args, **kwargs):
        raise gemini.GeminiErro("fora do ar")

    monkeypatch.setattr(gemini, "gerar_json", ia_quebrada)
    dados = checar(email="teste@exemplo.com").json()
    assert dados["origem_resumo"] == "regras"
    assert dados["resumo"].startswith("Encontramos 2 exposições")
