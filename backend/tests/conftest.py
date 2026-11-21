"""Configuração comum dos testes."""
import pytest

from app import config


@pytest.fixture(autouse=True)
def banco_isolado(tmp_path, monkeypatch):
    """Nenhum teste mexe no banco real (backend/alo_seguro.db): cada um usa um arquivo temporário."""
    monkeypatch.setattr(config, "CAMINHO_BANCO", tmp_path / "teste.db")
