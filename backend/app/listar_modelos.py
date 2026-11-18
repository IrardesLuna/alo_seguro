"""Mostra os modelos do Gemini liberados para a sua chave.

Uso (dentro da pasta backend, com o ambiente ativado):
    python -m app.listar_modelos
"""
from . import config, gemini

if __name__ == "__main__":
    if not gemini.configurado():
        print("Configure GEMINI_API_KEY no arquivo backend/.env primeiro.")
    else:
        print(f"Modelo configurado agora: {config.GEMINI_MODEL}\n")
        for nome in gemini.listar_modelos():
            if "flash" in nome:
                print("  ", nome)
        print("\nPara trocar, edite GEMINI_MODEL no backend/.env.")
