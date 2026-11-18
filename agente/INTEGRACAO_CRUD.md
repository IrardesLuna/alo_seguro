# Integração do analisador com o CRUD de casos reais

Documento para quem vai construir o CRUD. O analisador de mensagens já está pronto e **já sabe
usar casos reais**. Falta só a parte de guardar e moderar esses casos.

## Como funciona hoje

```
Usuário cola a mensagem
   └─▶ backend/app/anonimizar.py   oculta CPF, telefone, e-mail, cartão…
   └─▶ backend/app/heuristica.py   regras: táticas + nota
   └─▶ backend/app/similares.py    busca até 5 casos confirmados parecidos  ◀── o CRUD alimenta isto
   └─▶ backend/app/gemini.py       IA analisa com o prompt + base + casos parecidos
```

Hoje `similares.carregar_casos()` lê o arquivo
[`agente/casos_reais/casos_confirmados.json`](casos_reais/casos_confirmados.json), que está vazio.
Dá para testar o aprendizado colocando casos nesse arquivo à mão, no formato abaixo.

**O analisador não guarda nada** do que o usuário cola: essa é a promessa de privacidade do projeto.
Guardar casos só pode acontecer com **consentimento explícito** (ver
[aprendizado_continuo.md](aprendizado_continuo.md)).

## O que o CRUD precisa guardar

### Tabela `casos` (o mínimo para o agente aprender)

| Campo | Tipo | Regra |
|---|---|---|
| `id` | texto ou inteiro | único |
| `plataforma` | texto | `redes_sociais`, `email` ou `links` (as 3 opções da tela). Se souber a rede exata, pode usar `whatsapp`, `instagram`, `snapchat` ou `discord`: a busca de "redes sociais" encontra todas |
| `texto` | texto | **sempre anonimizado** com `app.anonimizar.anonimizar()` antes de salvar; até 500 caracteres são usados no prompt |
| `rotulo` | texto | `golpe` ou `nao_golpe` |
| `taticas` | lista de textos | só ids que existem em [`taxonomia.json`](taxonomia.json) |
| `golpe_base` | texto ou vazio | id da base (`wa001`, `ig014`…) se parecer com um golpe conhecido |
| `licao` | texto | frase curta escrita pelo moderador |
| `status` | texto | `pendente`, `aprovado` ou `rejeitado`; **só `aprovado` vai para a IA** |
| `reservado_para_teste` | sim/não | ~20% dos aprovados; esses **não** vão para a IA (servem para medir acertos) |
| `criado_em` / `atualizado_em` | data e hora | |

Formato que `similares.py` espera (um item da lista `casos`):

```json
{
  "id": "caso_0107",
  "plataforma": "whatsapp",
  "texto": "Oi mãe, esse é meu número novo... Pix de 1.850 para [CHAVE_PIX]",
  "rotulo": "golpe",
  "taticas": ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro", "urgencia"],
  "golpe_base": "wa001",
  "licao": "Golpista citou um boleto com horário limite para criar pressa.",
  "reservado_para_teste": false
}
```

### Operações do CRUD

| Operação | Para quê |
|---|---|
| **Criar** | o moderador cadastra um caso (ou ele chega do feedback do usuário como `pendente`) |
| **Listar** | fila de moderação, com filtro por `status` e `plataforma` |
| **Editar** | corrigir texto anonimizado, rótulo, táticas e lição; aprovar ou rejeitar |
| **Excluir** | apagar casos (inclusive a pedido do usuário, por causa da LGPD) |

## Como ligar o CRUD ao analisador

Basta trocar **uma função** em `backend/app/similares.py`. Exemplo com SQLite:

```python
import json
import sqlite3

def carregar_casos() -> list[dict]:
    with sqlite3.connect("alo_seguro.db") as conexao:
        conexao.row_factory = sqlite3.Row
        linhas = conexao.execute(
            "SELECT id, plataforma, texto, rotulo, taticas, golpe_base, licao, reservado_para_teste "
            "FROM casos WHERE status = 'aprovado'"
        ).fetchall()
    casos = []
    for linha in linhas:
        caso = dict(linha)
        caso["taticas"] = json.loads(caso["taticas"])  # guardado como texto JSON
        casos.append(caso)
    return casos
```

O resto (busca dos parecidos, formatação para o prompt e proteção contra instruções escondidas
no texto) já está pronto e testado em `backend/tests/test_api.py::test_casos_similares_entram_no_prompt`.

## Dados úteis que a API já devolve

Cada resposta de `POST /api/analisar` traz campos que o CRUD pode aproveitar quando houver
consentimento:

- `taticas_detectadas`: sugestão inicial das táticas do caso;
- `golpe_parecido.id`: sugestão de `golpe_base`;
- `possivel_golpe_novo`: `true` quando a IA acha que é um golpe que ainda não está na base.
  Esses casos alimentam o [prompt_novo_golpe.md](prompt_novo_golpe.md);
- `probabilidade_golpe`: para comparar com o rótulo final e medir acertos (falsos negativos e
  falsos positivos).
