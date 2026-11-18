"""Configurações lidas do arquivo backend/.env (nunca coloque chaves no código)."""
import os
from pathlib import Path

from dotenv import load_dotenv

PASTA_BACKEND = Path(__file__).resolve().parent.parent
PASTA_PROJETO = PASTA_BACKEND.parent
PASTA_AGENTE = PASTA_PROJETO / "agente"
PASTA_FRONTEND = PASTA_PROJETO / "projeto1-acessibilidade-corrigido" / "projeto1"

load_dotenv(PASTA_BACKEND / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# Lista de modelos separados por vírgula: se o primeiro estiver sobrecarregado, tenta o próximo.
# Os modelos padrão entram no fim da lista como reserva.
_MODELOS_PADRAO = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.1-flash-lite"]
GEMINI_RODADAS = 2          # quantas vezes percorre a lista de modelos
GEMINI_ESPERA_SEGUNDOS = 3  # pausa entre uma rodada e outra
GEMINI_TEMPO_MAXIMO = 45    # segundos no total; depois disso, usa as regras automáticas
_MODELOS_DO_ENV = [m.strip() for m in os.getenv("GEMINI_MODEL", "").split(",") if m.strip()]
GEMINI_MODELOS = _MODELOS_DO_ENV + [m for m in _MODELOS_PADRAO if m not in _MODELOS_DO_ENV]
GEMINI_MODEL = GEMINI_MODELOS[0]
GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "60"))
LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "10"))

TAMANHO_MINIMO_TEXTO = 3
TAMANHO_MAXIMO_TEXTO = 6000
