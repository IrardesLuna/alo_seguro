"""Testes do CRUD de casos reais (moderação) e da ligação com o agente."""
import pytest
from fastapi.testclient import TestClient

from app import config, main, similares

cliente = TestClient(main.app)
URL = "/api/v1/admin/casos"


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CAMINHO_BANCO", tmp_path / "teste.db")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(main, "HOSTS_LOCAIS", main.HOSTS_LOCAIS | {"testclient"})  # o TestClient não é 127.0.0.1


def novo_caso(**mudancas):
    caso = {"plataforma": "whatsapp", "texto": "Oi mãe, número novo. Faz um Pix pro meu CPF 123.456.789-00?",
            "rotulo": "golpe", "taticas": ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro"],
            "golpe_base": "wa001", "licao": "Clássico número novo.", "status": "pendente"}
    caso.update(mudancas)
    return cliente.post(URL, json=caso)


def test_criar_anonimiza_e_obter():
    resposta = novo_caso()
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["dados_ocultados"] == 1
    caso = corpo["caso"]
    assert "123.456.789-00" not in caso["texto"] and "[CPF]" in caso["texto"]
    assert caso["taticas"] == ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro"]
    assert cliente.get(f"{URL}/{caso['id']}").json()["licao"] == "Clássico número novo."


def test_listar_com_filtros_e_contagem():
    novo_caso()
    novo_caso(status="aprovado", plataforma="email", texto="Sua conta será bloqueada, clique aqui")
    novo_caso(status="rejeitado", texto="Oi, tudo bem?", rotulo="nao_golpe", taticas=[], golpe_base=None)
    tudo = cliente.get(URL).json()
    assert tudo["total"] == 3
    assert tudo["contagem"] == {"pendente": 1, "aprovado": 1, "rejeitado": 1}
    assert cliente.get(URL, params={"status": "aprovado"}).json()["total"] == 1
    assert cliente.get(URL, params={"plataforma": "email"}).json()["total"] == 1
    assert cliente.get(URL, params={"busca": "bloqueada"}).json()["total"] == 1


def test_editar_so_os_campos_enviados():
    caso = novo_caso().json()["caso"]
    editado = cliente.patch(f"{URL}/{caso['id']}", json={"status": "aprovado", "golpe_base": None}).json()["caso"]
    assert editado["status"] == "aprovado" and editado["golpe_base"] is None
    assert editado["licao"] == caso["licao"] and editado["texto"] == caso["texto"]


def test_excluir():
    caso = novo_caso().json()["caso"]
    assert cliente.delete(f"{URL}/{caso['id']}").status_code == 204
    assert cliente.get(f"{URL}/{caso['id']}").status_code == 404
    assert cliente.delete(f"{URL}/{caso['id']}").status_code == 404


@pytest.mark.parametrize("mudanca", [
    {"plataforma": "orkut"},
    {"texto": "  "},
    {"rotulo": "talvez"},
    {"taticas": ["tatica_inventada"]},
    {"golpe_base": "zz999"},
    {"status": "publicado"},
    {"licao": "x" * 301},
])
def test_validacoes(mudanca):
    assert novo_caso(**mudanca).status_code == 422


def test_editar_caso_inexistente():
    assert cliente.patch(f"{URL}/999", json={"status": "aprovado"}).status_code == 404


def test_sugestao_preenche_o_formulario():
    dados = cliente.post(f"{URL}/sugestao", json={
        "plataforma": "whatsapp", "texto": "me passa o código que chegou aí, meu número é (81) 99876-5432"}).json()
    assert "pedido_de_codigo" in dados["taticas"]
    assert "[TELEFONE]" in dados["texto"] and dados["dados_ocultados"] == 1
    assert dados["rotulo_sugerido"] == "golpe"


def test_opcoes():
    dados = cliente.get("/api/v1/admin/opcoes").json()
    assert len(dados["taticas"]) == 25 and len(dados["golpes"]) == 613
    assert {"id": "redes_sociais", "nome": "Mensagem de rede social"} in dados["plataformas"]


def test_moderacao_recusa_pedido_de_fora(monkeypatch):
    monkeypatch.setattr(main, "HOSTS_LOCAIS", {"127.0.0.1"})
    assert cliente.get(URL).status_code == 403
    assert novo_caso().status_code == 403


def test_so_aprovado_e_nao_reservado_chega_ao_agente():
    novo_caso(status="aprovado")
    novo_caso(status="pendente")
    novo_caso(status="aprovado", reservado_para_teste=True)
    carregados = similares.carregar_casos()
    assert sorted(c["status"] for c in carregados) == ["aprovado", "aprovado"]  # pendente fica de fora
    achados = similares.buscar("redes_sociais", {"troca_de_canal", "pedido_de_dinheiro", "personificacao_conhecido"},
                               "mãe, meu número novo, faz um pix")
    assert len(achados) == 1  # o reservado para teste não vai para a IA
    assert achados[0]["id"].startswith("caso_")
    assert '<caso id="caso_' in similares.formatar_para_prompt(achados)
