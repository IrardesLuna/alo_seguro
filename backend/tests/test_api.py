"""Testes da API, simulando a IA (não gasta a cota gratuita do Gemini)."""
import pytest
from fastapi.testclient import TestClient

from app import agente, config, gemini, main, similares

cliente = TestClient(main.app)


@pytest.fixture(autouse=True)
def limpar_limite():
    main._pedidos_por_ip.clear()


@pytest.fixture
def ia_ligada(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "chave-de-teste")


@pytest.fixture
def ia_desligada(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")


def test_saude():
    resposta = cliente.get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_tela_tem_3_opcoes_com_mais_de_100_golpes_cada():
    resposta = cliente.get("/api/plataformas").json()
    assert [p["id"] for p in resposta] == ["redes_sociais", "email", "links"]
    assert all(p["total_golpes"] > 100 for p in resposta)
    assert resposta[0]["total_golpes"] == 409  # WhatsApp + Instagram + Snapchat + Discord


def test_redes_sociais_usa_as_4_bases_no_prompt():
    prompt = agente.montar_prompt_sistema("redes_sociais", "")
    assert "{{" not in prompt
    assert "id | nome | táticas | sinais" in prompt
    for prefixo in ("wa001 |", "ig001 |", "sc001 |", "dc001 |"):
        assert prefixo in prompt
    assert "Facebook" in prompt and "LinkedIn" in prompt


def test_analisar_rede_social(ia_desligada):
    corpo = {"plataforma": "redes_sociais", "texto": "Oi mãe, troquei de número. Faz um Pix pra mim? Não posso atender agora."}
    dados = cliente.post("/api/analisar", json=corpo).json()
    assert dados["probabilidade_golpe"] >= 85
    assert dados["golpe_parecido"]["id"] == "wa001"


def test_site_abre():
    assert cliente.get("/").status_code == 200
    assert "Alô Seguro" in cliente.get("/proj1.html").text


def test_sem_ia_usa_regras(ia_desligada):
    resposta = cliente.post("/api/analisar", json={"plataforma": "whatsapp", "texto": "me passa o código que chegou aí"})
    dados = resposta.json()
    assert resposta.status_code == 200
    assert dados["origem"] == "regras"
    assert dados["probabilidade_golpe"] >= 90
    assert dados["aviso_sistema"]


def test_com_ia_corrige_resposta_fora_do_padrao(ia_ligada, monkeypatch):
    def ia_falsa(prompt, mensagem, esquema=None):
        assert "<mensagem_recebida>" in mensagem and "[TELEFONE]" in mensagem  # telefone ocultado
        assert "{{" not in prompt
        return {"probabilidade_golpe": 100, "taticas_detectadas": ["urgencia", "tatica_inventada"],
                "golpe_parecido": {"id": "wa001", "similaridade": 140},
                "red_flags": [{"trecho": "agora", "tatica": "urgencia", "explicacao": "Pressa."}],
                "dicas": ["Ligue para o número antigo."]}

    monkeypatch.setattr(gemini, "gerar_json", ia_falsa)
    resposta = cliente.post("/api/analisar", json={"plataforma": "whatsapp", "texto": "Me liga agora no (81) 99876-5432"})
    dados = resposta.json()
    assert dados["origem"] == "ia"
    assert dados["probabilidade_golpe"] == 99          # nunca 100%
    assert dados["taticas_detectadas"] == ["urgencia"]   # tática inexistente removida
    assert dados["golpe_parecido"] == {"id": "wa001", "nome": "Golpe do número novo", "similaridade": 100}
    assert dados["dados_ocultados"] == 1


def test_ia_com_poucas_dicas_e_completada(ia_ligada, monkeypatch):
    monkeypatch.setattr(gemini, "gerar_json", lambda p, m, e=None: {"probabilidade_golpe": 3, "dicas": ["Tudo normal."]})
    dados = cliente.post("/api/analisar", json={"plataforma": "whatsapp", "texto": "Oi mãe, chego às 19h"}).json()
    assert dados["dicas"][0] == "Tudo normal."
    assert len(dados["dicas"]) >= 3


def test_ia_dando_zero_vira_um(ia_ligada, monkeypatch):
    monkeypatch.setattr(gemini, "gerar_json", lambda p, m, e=None: {"probabilidade_golpe": 0})
    dados = cliente.post("/api/analisar", json={"plataforma": "email", "texto": "Bom dia, tudo certo?"}).json()
    assert dados["probabilidade_golpe"] == 1


def test_ia_fora_do_ar_cai_para_regras(ia_ligada, monkeypatch):
    def ia_quebrada(prompt, mensagem, esquema=None):
        raise gemini.GeminiErro("O limite gratuito da IA foi atingido.")

    monkeypatch.setattr(gemini, "gerar_json", ia_quebrada)
    dados = cliente.post("/api/analisar", json={"plataforma": "links", "texto": "https://nike-outlet-oficial.shop"}).json()
    assert dados["origem"] == "regras"
    assert "limite gratuito" in dados["aviso_sistema"]
    assert dados["analise_link"][0]["tipo"] == "loja_falsa"


def test_modelo_sobrecarregado_tenta_o_proximo(ia_ligada, monkeypatch):
    chamados = []

    class RespostaFalsa:
        def __init__(self, status, dados):
            self.status_code, self._dados, self.text = status, dados, str(dados)

        def json(self):
            return self._dados

    def post_falso(url, **kwargs):
        chamados.append(url.split("/models/")[1].split(":")[0])
        if len(chamados) == 1:
            return RespostaFalsa(503, {"error": {"message": "high demand"}})
        texto = '{"probabilidade_golpe": 70, "veredito": "Suspeito."}'
        return RespostaFalsa(200, {"candidates": [{"content": {"parts": [{"text": texto}]}}]})

    monkeypatch.setattr(config, "GEMINI_MODELOS", ["modelo-cheio", "modelo-livre"])
    monkeypatch.setattr(gemini.httpx, "post", post_falso)
    assert gemini.gerar_json("prompt", "mensagem")["probabilidade_golpe"] == 70
    assert chamados == ["modelo-cheio", "modelo-livre"]


@pytest.mark.parametrize("corpo", [
    {"plataforma": "telegram", "texto": "oi"},
    {"plataforma": "whatsapp", "texto": "  "},
    {"plataforma": "whatsapp", "texto": "a" * 6001},
])
def test_pedidos_invalidos(corpo):
    assert cliente.post("/api/analisar", json=corpo).status_code == 422


def test_limite_por_minuto(ia_desligada, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_POR_MINUTO", 2)
    corpo = {"plataforma": "whatsapp", "texto": "oi, tudo bem?"}
    assert cliente.post("/api/analisar", json=corpo).status_code == 200
    assert cliente.post("/api/analisar", json=corpo).status_code == 200
    assert cliente.post("/api/analisar", json=corpo).status_code == 429


def test_casos_similares_entram_no_prompt():
    casos = [
        {"id": "caso_1", "plataforma": "whatsapp", "rotulo": "golpe", "taticas": ["troca_de_canal", "pedido_de_dinheiro"],
         "texto": "Oi mãe, número novo, faz um pix", "licao": "Clássico número novo."},
        {"id": "caso_2", "plataforma": "whatsapp", "rotulo": "golpe", "reservado_para_teste": True,
         "taticas": ["troca_de_canal", "pedido_de_dinheiro"], "texto": "Oi mãe, número novo, faz um pix"},
        {"id": "caso_3", "plataforma": "email", "rotulo": "golpe", "taticas": ["troca_de_canal"], "texto": "número novo"},
    ]
    achados = similares.buscar("whatsapp", {"troca_de_canal", "pedido_de_dinheiro"}, "mãe, meu número novo, me faz um pix", casos)
    assert [c["id"] for c in achados] == ["caso_1"]  # ignora o reservado para teste e outra plataforma
    texto = similares.formatar_para_prompt(achados)
    assert '<caso id="caso_1" rotulo="golpe"' in texto and "Clássico número novo." in texto

    # "redes_sociais" também encontra casos guardados como "whatsapp"
    achados = similares.buscar("redes_sociais", {"troca_de_canal", "pedido_de_dinheiro"}, "mãe, meu número novo, me faz um pix", casos)
    assert [c["id"] for c in achados] == ["caso_1"]
