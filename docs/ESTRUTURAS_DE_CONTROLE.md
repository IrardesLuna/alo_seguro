# Estruturas condicionais e de repetição

Este documento mostra onde o código do Alô Seguro usa **estruturas condicionais** (decidem *se*
algo acontece: `if`, `elif`, `else`, ternário) e **estruturas de repetição** (fazem algo *várias
vezes*: `for`, `while`, `forEach`, compreensões de lista).

Os números de linha são clicáveis no GitHub. A tabela completa no fim deste arquivo foi gerada
automaticamente; se o código mudar, as linhas podem mudar também.

## Os melhores exemplos para apresentar

### 1. Repetição dentro de repetição: procurar golpes no texto
[`backend/app/heuristica.py`, linhas 367–372](../backend/app/heuristica.py#L367)

```python
for tatica, padroes in REGRAS_COMPILADAS.items():   # para cada uma das 25 táticas...
    for padrao in padroes:                           # ...testa cada padrão de frase
        achado = padrao.search(texto_normalizado)
        if achado:                                   # se encontrou,
            encontradas[tatica] = _trecho(...)       # guarda o trecho como prova
            break                                    # e passa para a próxima tática
```
**Por que importa:** é o "olho" do agente. O `for` externo percorre as táticas, o interno percorre
as frases típicas de cada uma, e o `break` evita trabalho repetido.

### 2. Condicionais que garantem a regra "nunca 0%"
[`backend/app/heuristica.py`, linhas 401–423](../backend/app/heuristica.py#L401)

```python
for tatica in taticas:                  # soma os pesos das táticas encontradas
    soma += pesos[tatica]["pontos"]
for combinacao in COMBINACOES:          # confere cada combinação perigosa
    if tem_todas and tem_alguma:        # se a mensagem tem a combinação,
        pisos_aplicados.append(...)     # a nota não pode ficar abaixo do piso
if not tem_pedido and not tem_forte:    # sem pedido, ainda não é golpe:
    nota = min(nota, 25)                # limite de 25%
nota = max(1, min(99, nota))            # nunca 0% e nunca 100%
```
A mesma trava existe para a resposta da IA em
[`backend/app/servico.py`, linha 32](../backend/app/servico.py#L32).

### 3. Cadeia de `if` para classificar o nível de risco
[`backend/app/heuristica.py`, linha 341](../backend/app/heuristica.py#L341)

```python
if nota <= 15:   return "baixo"
if nota <= 45:   return "medio"
if nota <= 79:   return "alto"
return "muito_alto"
```

### 4. `if / elif / else` para classificar um link
[`backend/app/links.py`, linhas 197–208](../backend/app/links.py#L197)

Decide se o link é *download perigoso*, *fraude financeira*, *loja falsa*, *roubo de dados*,
*provavelmente legítimo* ou *sem conclusão*. A ordem dos `elif` define a prioridade.

### 5. Repetição dupla para descobrir domínios que imitam marcas
[`backend/app/links.py`, linhas 81–90](../backend/app/links.py#L81)

A função `distancia_edicao` usa dois `for` aninhados para contar quantas letras separam
`rnercadolivre` de `mercadolivre` (algoritmo de Levenshtein). Se for só 1 letra, é imitação.

### 6. `for` com `continue` e `if`: buscar casos reais parecidos
[`backend/app/similares.py`, linhas 51–56](../backend/app/similares.py#L51)

```python
for caso in casos:
    if caso.get("plataforma") != plataforma or caso.get("reservado_para_teste"):
        continue                            # pula casos de outro canal ou reservados para teste
    semelhanca = 0.6 * ... + 0.4 * ...
    if semelhanca >= SEMELHANCA_MINIMA:     # só guarda os parecidos o bastante
        candidatos.append((semelhanca, caso))
```
É a base do aprendizado contínuo do agente.

### 7. `while` para controlar o limite de uso
[`backend/app/main.py`, linhas 41–43](../backend/app/main.py#L41)

```python
while fila and agora - fila[0] > 60:   # enquanto houver pedidos com mais de 60 s,
    fila.popleft()                     # remove da fila
if len(fila) >= config.LIMITE_POR_MINUTO:
    raise HTTPException(429, "Muitas análises seguidas...")
```

### 8. JavaScript: `forEach` para mostrar cada red flag
[`analisar.js`, linha 190](../frontend/projeto1/analisar.js#L190)

`dados.red_flags.forEach(...)` cria um cartão na tela para cada sinal de alerta que a IA encontrou.

### 9. JavaScript: `if / else if` para navegar nas abas pelo teclado
[`analisar.js`, linha 76](../frontend/projeto1/analisar.js#L76)

Seta para a direita, seta para a esquerda, Home e End mudam de aba (acessibilidade).

### 10. Código original do grupo
[`proj1.js`, linhas 133 e 197](../frontend/projeto1/proj1.js#L197)

`achados.forEach(...)` mostra cada vazamento encontrado, e `if (achados.length > 0) … else …`
escolhe entre a tela de "encontramos exposições" e a de "nada encontrado".

## Tabela completa
| Arquivo | Condicionais | Repetições |
| --- | --- | --- |
| `backend/app/main.py` | 4 | 2 |
| `backend/app/servico.py` | 15 | 8 |
| `backend/app/heuristica.py` | 37 | 25 |
| `backend/app/links.py` | 32 | 13 |
| `backend/app/anonimizar.py` | 0 | 2 |
| `backend/app/similares.py` | 9 | 6 |
| `backend/app/gemini.py` | 14 | 4 |
| `backend/app/agente.py` | 3 | 7 |
| `backend/app/config.py` | 0 | 2 |
| `backend/app/listar_modelos.py` | 4 | 1 |
| `frontend/projeto1/analisar.js` | 44 | 13 |
| `frontend/projeto1/proj1.js` | 15 | 4 |
| **Total** | **177** | **87** |

### `backend/app/main.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [41](../backend/app/main.py#L41) | Repetição `while` | `while fila and agora - fila[0] > 60:` |
| [43](../backend/app/main.py#L43) | Condicional `if`/`elif` | `if len(fila) >= config.LIMITE_POR_MINUTO:` |
| [57](../backend/app/main.py#L57) | Repetição `for` | `for chave, nome in agente.CANAIS.items()` |
| [66](../backend/app/main.py#L66) | Condicional `if`/`elif` | `if plataforma not in agente.PLATAFORMAS:` |
| [68](../backend/app/main.py#L68) | Condicional `if`/`elif` | `if len(texto) < config.TAMANHO_MINIMO_TEXTO:` |
| [70](../backend/app/main.py#L70) | Condicional `if`/`elif` | `if len(texto) > config.TAMANHO_MAXIMO_TEXTO:` |

### `backend/app/servico.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [11](../backend/app/servico.py#L11) | Condicional (ternário `x if c else y`) | `return str(valor).strip()[:limite] if valor is not None else ""` |
| [15](../backend/app/servico.py#L15) | Condicional `if`/`elif` | `if not isinstance(valor, list):` |
| [18](../backend/app/servico.py#L18) | Repetição `for` | `for item in valor:` |
| [19](../backend/app/servico.py#L19) | Condicional `if`/`elif` | `if isinstance(item, dict):  # ex.: {"passo_1": "..."} vira só o texto` |
| [20](../backend/app/servico.py#L20) | Repetição (compreensão / gerador) | `item = " ".join(str(v) for v in item.values() if v)` |
| [21](../backend/app/servico.py#L21) | Condicional `if`/`elif` | `if _texto(item):` |
| [35](../backend/app/servico.py#L35) | Repetição (compreensão / gerador) | `taticas = [t for t in bruto.get("taticas_detectadas", []) if t in taticas_validas]` |
| [38](../backend/app/servico.py#L38) | Repetição `for` | `for item in bruto.get("red_flags", []) if isinstance(bruto.get("red_flags"), list) else...` |
| [39](../backend/app/servico.py#L39) | Condicional `if`/`elif` | `if isinstance(item, dict) and _texto(item.get("explicacao")):` |
| [40](../backend/app/servico.py#L40) | Condicional (ternário `x if c else y`) | `tatica = item.get("tatica") if item.get("tatica") in taticas_validas else None` |
| [45](../backend/app/servico.py#L45) | Condicional `if`/`elif` | `if isinstance(parecido, dict) and parecido.get("id") in agente.golpes_por_id():` |
| [52](../backend/app/servico.py#L52) | Condicional `else` | `else:` |
| [56](../backend/app/servico.py#L56) | Repetição `for` | `for item in bruto.get("analise_link", []) if isinstance(bruto.get("analise_link"), list...` |
| [57](../backend/app/servico.py#L57) | Condicional `if`/`elif` | `if isinstance(item, dict) and item.get("url"):` |
| [61](../backend/app/servico.py#L61) | Condicional `if`/`elif` | `if not links:` |
| [66](../backend/app/servico.py#L66) | Repetição `for` | `for dica in regras["dicas"]:` |
| [67](../backend/app/servico.py#L67) | Condicional `if`/`elif` | `if len(dicas) >= 3:` |
| [69](../backend/app/servico.py#L69) | Condicional `if`/`elif` | `if dica not in dicas:` |
| [109](../backend/app/servico.py#L109) | Condicional `if`/`elif` | `if gemini.configurado():` |
| [118](../backend/app/servico.py#L118) | Condicional `else` | `else:` |
| [122](../backend/app/servico.py#L122) | Condicional `if`/`elif` | `if origem == "regras":` |
| [123](../backend/app/servico.py#L123) | Repetição (compreensão / gerador) | `resultado = {chave: valor for chave, valor in regras.items() if not chave.startswith("_")}` |
| [127](../backend/app/servico.py#L127) | Repetição (compreensão / gerador) | `{"id": t, "nome": nomes[t]["nome"], "peso": nomes[t]["peso"]} for t in resultado["tatic...` |

### `backend/app/heuristica.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [182](../backend/app/heuristica.py#L182) | Repetição (compreensão / gerador) | `REGRAS_COMPILADAS = {tatica: [re.compile(p) for p in padroes] for tatica, padroes in RE...` |
| [291](../backend/app/heuristica.py#L291) | Repetição (compreensão / gerador) | `contextos = [nome for nome, padrao in CONTEXTOS.items() if padrao.search(texto_normaliz...` |
| [292](../backend/app/heuristica.py#L292) | Condicional `if`/`elif` | `if tem_links:` |
| [294](../backend/app/heuristica.py#L294) | Condicional `if`/`elif` | `if plataforma == "email":` |
| [299](../backend/app/heuristica.py#L299) | Repetição `for` | `for contexto in contextos:` |
| [300](../backend/app/heuristica.py#L300) | Repetição `for` | `for dica in DICAS_CONFIRMACAO[contexto]:` |
| [301](../backend/app/heuristica.py#L301) | Condicional `if`/`elif` | `if dica not in dicas:` |
| [324](../backend/app/heuristica.py#L324) | Repetição `for` | `for caractere in texto:` |
| [325](../backend/app/heuristica.py#L325) | Condicional (ternário `x if c else y`) | `base = unicodedata.normalize("NFKD", caractere)[0] if caractere else caractere` |
| [333](../backend/app/heuristica.py#L333) | Repetição `while` | `while inicio > 0 and not original[inicio - 1].isspace():` |
| [335](../backend/app/heuristica.py#L335) | Repetição `while` | `while fim < len(original) and not original[fim].isspace():` |
| [338](../backend/app/heuristica.py#L338) | Condicional (ternário `x if c else y`) | `return trecho if len(trecho) <= 120 else trecho[:117] + "..."` |
| [342](../backend/app/heuristica.py#L342) | Condicional `if`/`elif` | `if nota <= 15:` |
| [344](../backend/app/heuristica.py#L344) | Condicional `if`/`elif` | `if nota <= 45:` |
| [346](../backend/app/heuristica.py#L346) | Condicional `if`/`elif` | `if nota <= 79:` |
| [352](../backend/app/heuristica.py#L352) | Condicional `if`/`elif` | `if not a or not b:` |
| [367](../backend/app/heuristica.py#L367) | Repetição `for` | `for tatica, padroes in REGRAS_COMPILADAS.items():` |
| [368](../backend/app/heuristica.py#L368) | Repetição `for` | `for padrao in padroes:` |
| [370](../backend/app/heuristica.py#L370) | Condicional `if`/`elif` | `if achado:` |
| [374](../backend/app/heuristica.py#L374) | Repetição `for` | `for link in links:` |
| [375](../backend/app/heuristica.py#L375) | Condicional `if`/`elif` | `if link["suspeito"] and "link_suspeito" not in encontradas:` |
| [377](../backend/app/heuristica.py#L377) | Condicional `if`/`elif` | `if link["tipo"] == "download_malicioso" and "arquivo_malicioso" not in encontradas:` |
| [379](../backend/app/heuristica.py#L379) | Condicional `if`/`elif` | `if link["imita_marca"] and "personificacao_instituicao" not in encontradas:` |
| [387](../backend/app/heuristica.py#L387) | Repetição `for` | `for link in links:` |
| [388](../backend/app/heuristica.py#L388) | Condicional `if`/`elif` | `if link["imita_marca"]:` |
| [390](../backend/app/heuristica.py#L390) | Condicional `if`/`elif` | `if link["tipo"] == "download_malicioso":` |
| [392](../backend/app/heuristica.py#L392) | Condicional `if`/`elif` | `if len(link["motivos"]) >= 2:` |
| [401](../backend/app/heuristica.py#L401) | Repetição `for` | `for tatica in taticas:` |
| [406](../backend/app/heuristica.py#L406) | Repetição `for` | `for combinacao in COMBINACOES:` |
| [409](../backend/app/heuristica.py#L409) | Condicional `if`/`elif` | `if tem_todas and tem_alguma:` |
| [413](../backend/app/heuristica.py#L413) | Condicional `if`/`elif` | `if pisos_aplicados:` |
| [414](../backend/app/heuristica.py#L414) | Repetição (compreensão / gerador) | `nota = max(nota, max(c["piso"] for c in pisos_aplicados))` |
| [415](../backend/app/heuristica.py#L415) | Condicional `if`/`elif` | `if len(pisos_aplicados) >= 2:` |
| [418](../backend/app/heuristica.py#L418) | Repetição (compreensão / gerador) | `tem_pedido = bool(presentes & TATICAS_DE_PEDIDO) or any(p.startswith("_") for p in pres...` |
| [419](../backend/app/heuristica.py#L419) | Repetição (compreensão / gerador) | `tem_forte = any(pesos[t]["peso"] == "forte" for t in taticas)` |
| [420](../backend/app/heuristica.py#L420) | Condicional `if`/`elif` | `if not tem_pedido and not tem_forte:` |
| [424](../backend/app/heuristica.py#L424) | Repetição (compreensão / gerador) | `return {"nota": nota, "soma": soma, "pisos": [c["nome"] for c in pisos_aplicados]}` |
| [441](../backend/app/heuristica.py#L441) | Repetição `for` | `for marca in MARCAS_NOS_NOMES:` |
| [442](../backend/app/heuristica.py#L442) | Condicional `if`/`elif` | `if marca in nome and marca not in texto_normalizado:` |
| [449](../backend/app/heuristica.py#L449) | Repetição (compreensão / gerador) | `return {palavra[:5] for palavra in re.findall(r"[a-z]{4,}", texto_normalizado)}` |
| [454](../backend/app/heuristica.py#L454) | Condicional `if`/`elif` | `if len(taticas) < 2:` |
| [458](../backend/app/heuristica.py#L458) | Repetição `for` | `for golpe in agente.base_golpes(plataforma):` |
| [459](../backend/app/heuristica.py#L459) | Condicional `if`/`elif` | `if _marca_incompativel(golpe["nome"], texto_normalizado):` |
| [463](../backend/app/heuristica.py#L463) | Condicional `if`/`elif` | `if em_comum == 0:` |
| [466](../backend/app/heuristica.py#L466) | Condicional `if`/`elif` | `if nota > melhor_nota:` |
| [468](../backend/app/heuristica.py#L468) | Condicional `if`/`elif` | `if melhor is None or melhor_nota < 0.5:` |
| [480](../backend/app/heuristica.py#L480) | Condicional `if`/`elif` | `if REGEX_SEED.search(texto_normalizado):` |
| [482](../backend/app/heuristica.py#L482) | Condicional `if`/`elif` | `if REGEX_EXECUTAVEL.search(texto_normalizado):` |
| [484](../backend/app/heuristica.py#L484) | Condicional `if`/`elif` | `if REGEX_INJECAO.search(texto_normalizado):` |
| [494](../backend/app/heuristica.py#L494) | Repetição `for` | `for t in ordenadas[:6]` |
| [501](../backend/app/heuristica.py#L501) | Condicional `if`/`elif` | `if parecido:` |
| [504](../backend/app/heuristica.py#L504) | Repetição (compreensão / gerador) | `candidatas += [pesos[t]["dica_padrao"] for t in ordenadas]` |
| [507](../backend/app/heuristica.py#L507) | Repetição `for` | `for dica in candidatas:` |
| [508](../backend/app/heuristica.py#L508) | Condicional `if`/`elif` | `if dica not in dicas:` |
| [510](../backend/app/heuristica.py#L510) | Condicional `if`/`elif` | `if len(dicas) >= 5:` |
| [520](../backend/app/heuristica.py#L520) | Condicional `if`/`elif` | `if parecido and nivel in ("alto", "muito_alto"):` |
| [522](../backend/app/heuristica.py#L522) | Condicional `if`/`elif` | `if not taticas and links and all(l["tipo"] == "legitimo_provavel" for l in links):` |
| [525](../backend/app/heuristica.py#L525) | Condicional `if`/`elif` | `if taticas:` |
| [526](../backend/app/heuristica.py#L526) | Repetição (compreensão / gerador) | `nomes = ", ".join(pesos[t]["nome"].lower() for t in ordenadas[:4])` |
| [528](../backend/app/heuristica.py#L528) | Condicional `else` | `else:` |
| [530](../backend/app/heuristica.py#L530) | Condicional `if`/`elif` | `if calculo["pisos"]:` |
| [552](../backend/app/heuristica.py#L552) | Repetição `for` | `for l in links` |

### `backend/app/links.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [75](../backend/app/links.py#L75) | Repetição `for` | `for sufixo in SUFIXOS_DUPLOS:` |
| [76](../backend/app/links.py#L76) | Condicional `if`/`elif` | `if host.endswith("." + sufixo) or host == sufixo:` |
| [84](../backend/app/links.py#L84) | Repetição `for` | `for i, letra_a in enumerate(a, start=1):` |
| [86](../backend/app/links.py#L86) | Repetição `for` | `for j, letra_b in enumerate(b, start=1):` |
| [87](../backend/app/links.py#L87) | Condicional (ternário `x if c else y`) | `custo = 0 if letra_a == letra_b else 1` |
| [101](../backend/app/links.py#L101) | Condicional (ternário `x if c else y`) | `url_completa = url if re.match(r"^https?://", url, re.IGNORECASE) else "http://" + url` |
| [109](../backend/app/links.py#L109) | Condicional `if`/`elif` | `if "@" in netloc:` |
| [116](../backend/app/links.py#L116) | Condicional (ternário `x if c else y`) | `extensao = host.rsplit(".", 1)[-1] if "." in host else ""` |
| [124](../backend/app/links.py#L124) | Condicional `if`/`elif` | `if host.startswith("xn--") or ".xn--" in host:` |
| [127](../backend/app/links.py#L127) | Condicional `if`/`elif` | `if dominio in ENCURTADORES:` |
| [129](../backend/app/links.py#L129) | Condicional `if`/`elif` | `if extensao in EXTENSOES_SUSPEITAS:` |
| [132](../backend/app/links.py#L132) | Repetição `for` | `for hospedagem in HOSPEDAGEM_GENERICA:` |
| [133](../backend/app/links.py#L133) | Condicional `if`/`elif` | `if host == hospedagem or host.endswith("." + hospedagem):` |
| [137](../backend/app/links.py#L137) | Condicional `if`/`elif` | `if host.count(".") >= 4:` |
| [139](../backend/app/links.py#L139) | Condicional `if`/`elif` | `if partes.scheme == "http" and re.match(r"^http://", url, re.IGNORECASE):` |
| [143](../backend/app/links.py#L143) | Condicional `if`/`elif` | `if caminho.endswith(DOWNLOADS):` |
| [146](../backend/app/links.py#L146) | Repetição `for` | `for chave in ("redirect", "url", "next", "redir", "goto"):` |
| [147](../backend/app/links.py#L147) | Condicional `if`/`elif` | `if any(valor.startswith("http") for valor in consulta.get(chave, [])):` |
| [153](../backend/app/links.py#L153) | Repetição (compreensão / gerador) | `pedacos = [p for p in re.split(r"[.-]", host) if p]` |
| [154](../backend/app/links.py#L154) | Condicional `if`/`elif` | `if hospedagem_generica:` |
| [155](../backend/app/links.py#L155) | Repetição (compreensão / gerador) | `pedacos += [p for p in re.split(r"[/._-]", caminho) if p]` |
| [159](../backend/app/links.py#L159) | Condicional `if`/`elif` | `if not hospedagem_generica:` |
| [160](../backend/app/links.py#L160) | Repetição `for` | `for marca, oficiais in DOMINIOS_OFICIAIS.items():` |
| [161](../backend/app/links.py#L161) | Condicional `if`/`elif` | `if dominio in oficiais:` |
| [167](../backend/app/links.py#L167) | Condicional `if`/`elif` | `if marca_oficial is None:` |
| [168](../backend/app/links.py#L168) | Repetição `for` | `for marca in DOMINIOS_OFICIAIS:` |
| [169](../backend/app/links.py#L169) | Repetição (compreensão / gerador) | `usa_nome_da_marca = any(p == marca or p.startswith(marca) for p in pedacos)` |
| [170](../backend/app/links.py#L170) | Condicional `if`/`elif` | `if usa_nome_da_marca:` |
| [172](../backend/app/links.py#L172) | Condicional `if`/`elif` | `if hospedagem_generica:` |
| [174](../backend/app/links.py#L174) | Condicional `else` | `else:` |
| [178](../backend/app/links.py#L178) | Condicional `if`/`elif` | `if len(marca) >= 6:` |
| [180](../backend/app/links.py#L180) | Repetição `for` | `for pedaco in [nome_dominio] + pedacos:` |
| [181](../backend/app/links.py#L181) | Condicional `if`/`elif` | `if pedaco != marca and (_normalizar_imitacao(pedaco) == marca or distancia_edicao(pedac...` |
| [184](../backend/app/links.py#L184) | Condicional `if`/`elif` | `if imitacao:` |
| [190](../backend/app/links.py#L190) | Condicional `if`/`elif` | `if eh_governo:` |
| [192](../backend/app/links.py#L192) | Condicional `if`/`elif` | `elif any(p in PALAVRAS_DE_GOVERNO or p.startswith(("govbr", "receita", "inss", "detran"...` |
| [197](../backend/app/links.py#L197) | Condicional `if`/`elif` | `if motivos and caminho.endswith(DOWNLOADS):` |
| [199](../backend/app/links.py#L199) | Condicional `if`/`elif` | `elif motivos and (any(p in texto_url for p in PALAVRAS_FINANCEIRAS)):` |
| [201](../backend/app/links.py#L201) | Condicional `if`/`elif` | `elif motivos and (any(p in texto_url for p in PALAVRAS_LOJA) or extensao in ("shop", "s...` |
| [203](../backend/app/links.py#L203) | Condicional `if`/`elif` | `elif motivos and (marca_imitada or endereco_enganoso or any(p in texto_url for p in PAL...` |
| [205](../backend/app/links.py#L205) | Condicional `if`/`elif` | `elif not motivos and sinais_bons:` |
| [207](../backend/app/links.py#L207) | Condicional `else` | `else:` |
| [223](../backend/app/links.py#L223) | Repetição `for` | `for encontrado in REGEX_URL.finditer(texto):` |
| [225](../backend/app/links.py#L225) | Condicional `if`/`elif` | `if url and url.lower() not in [v.lower() for v in vistos]:` |
| [231](../backend/app/links.py#L231) | Repetição (compreensão / gerador) | `return [analisar_url(url) for url in encontrar_links(texto)]` |

### `backend/app/anonimizar.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [24](../backend/app/anonimizar.py#L24) | Repetição `for` | `for marcador, padrao in PADROES:` |
| [35](../backend/app/anonimizar.py#L35) | Repetição `for` | `for link in REGEX_URL.finditer(texto):` |

### `backend/app/similares.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [28](../backend/app/similares.py#L28) | Repetição (compreensão / gerador) | `return {p for p in palavras if p not in PALAVRAS_VAZIAS}` |
| [32](../backend/app/similares.py#L32) | Condicional `if`/`elif` | `if not ARQUIVO_CASOS.exists():` |
| [40](../backend/app/similares.py#L40) | Condicional `if`/`elif` | `if casos is None:` |
| [45](../backend/app/similares.py#L45) | Condicional `if`/`elif` | `if plataforma in ("redes_sociais",) + REDES_SOCIAIS:` |
| [47](../backend/app/similares.py#L47) | Condicional `else` | `else:` |
| [51](../backend/app/similares.py#L51) | Repetição `for` | `for caso in casos:` |
| [52](../backend/app/similares.py#L52) | Condicional `if`/`elif` | `if caso.get("plataforma") not in aceitas or caso.get("reservado_para_teste"):` |
| [56](../backend/app/similares.py#L56) | Condicional `if`/`elif` | `if semelhanca >= SEMELHANCA_MINIMA:` |
| [62](../backend/app/similares.py#L62) | Repetição (compreensão / gerador) | `tem_nao_golpe = any(caso.get("rotulo") == "nao_golpe" for _, caso in escolhidos)` |
| [63](../backend/app/similares.py#L63) | Condicional `if`/`elif` | `if not tem_nao_golpe and len(escolhidos) == MAXIMO_CASOS:` |
| [64](../backend/app/similares.py#L64) | Repetição `for` | `for par in candidatos[MAXIMO_CASOS:]:` |
| [65](../backend/app/similares.py#L65) | Condicional `if`/`elif` | `if par[1].get("rotulo") == "nao_golpe":` |
| [69](../backend/app/similares.py#L69) | Repetição (compreensão / gerador) | `return [dict(caso, semelhanca=round(semelhanca, 2)) for semelhanca, caso in escolhidos]` |
| [73](../backend/app/similares.py#L73) | Condicional `if`/`elif` | `if not casos:` |
| [76](../backend/app/similares.py#L76) | Repetição `for` | `for caso in casos:` |

### `backend/app/gemini.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [32](../backend/app/gemini.py#L32) | Condicional `if`/`elif` | `if inicio == -1 or fim == -1:` |
| [47](../backend/app/gemini.py#L47) | Condicional `if`/`elif` | `if resposta.status_code in (500, 502, 503, 504):` |
| [49](../backend/app/gemini.py#L49) | Condicional `if`/`elif` | `if resposta.status_code == 429:` |
| [51](../backend/app/gemini.py#L51) | Condicional `if`/`elif` | `if resposta.status_code == 404:` |
| [54](../backend/app/gemini.py#L54) | Condicional `if`/`elif` | `if resposta.status_code == 403 and "free tier" in resposta.text.lower():` |
| [57](../backend/app/gemini.py#L57) | Condicional `if`/`elif` | `if resposta.status_code in (400, 401, 403) and "api key" in resposta.text.lower():` |
| [59](../backend/app/gemini.py#L59) | Condicional `if`/`elif` | `if resposta.status_code in (401, 403):` |
| [61](../backend/app/gemini.py#L61) | Condicional `if`/`elif` | `if resposta.status_code >= 400:` |
| [70](../backend/app/gemini.py#L70) | Repetição (compreensão / gerador) | `texto = "".join(parte.get("text", "") for parte in partes if not parte.get("thought"))` |
| [73](../backend/app/gemini.py#L73) | Condicional `if`/`elif` | `if motivo:` |
| [83](../backend/app/gemini.py#L83) | Condicional `if`/`elif` | `if not configurado():` |
| [87](../backend/app/gemini.py#L87) | Condicional `if`/`elif` | `if esquema:` |
| [100](../backend/app/gemini.py#L100) | Repetição `for` | `for rodada in range(config.GEMINI_RODADAS):` |
| [101](../backend/app/gemini.py#L101) | Condicional `if`/`elif` | `if rodada > 0:` |
| [103](../backend/app/gemini.py#L103) | Repetição `for` | `for modelo in config.GEMINI_MODELOS:` |
| [105](../backend/app/gemini.py#L105) | Condicional `if`/`elif` | `if tempo_restante < 3:` |
| [119](../backend/app/gemini.py#L119) | Repetição `for` | `for modelo in resposta.json().get("models", []):` |
| [120](../backend/app/gemini.py#L120) | Condicional `if`/`elif` | `if "generateContent" in modelo.get("supportedGenerationMethods", []):` |

### `backend/app/agente.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [27](../backend/app/agente.py#L27) | Repetição (compreensão / gerador) | `PLATAFORMAS = {**CANAIS, **{rede: BASES[rede] for rede in REDES_SOCIAIS}}` |
| [95](../backend/app/agente.py#L95) | Repetição (compreensão / gerador) | `return {t["id"]: t for t in taxonomia()["taticas"]}` |
| [106](../backend/app/agente.py#L106) | Condicional `if`/`elif` | `if plataforma == "redes_sociais":` |
| [108](../backend/app/agente.py#L108) | Repetição `for` | `for rede in REDES_SOCIAIS:` |
| [121](../backend/app/agente.py#L121) | Condicional `if`/`elif` | `if plataforma != "redes_sociais":` |
| [124](../backend/app/agente.py#L124) | Repetição `for` | `for golpe in base_golpes("redes_sociais"):` |
| [132](../backend/app/agente.py#L132) | Repetição `for` | `for base in BASES:` |
| [133](../backend/app/agente.py#L133) | Repetição `for` | `for golpe in base_golpes(base):` |
| [143](../backend/app/agente.py#L143) | Condicional `if`/`elif` | `if inicio == -1 or fim == -1:` |
| [156](../backend/app/agente.py#L156) | Repetição `for` | `for marcador, valor in substituicoes.items():` |

### `backend/app/config.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [21](../backend/app/config.py#L21) | Repetição (compreensão / gerador) | `_MODELOS_DO_ENV = [m.strip() for m in os.getenv("GEMINI_MODEL", "").split(",") if m.str...` |
| [22](../backend/app/config.py#L22) | Repetição (compreensão / gerador) | `GEMINI_MODELOS = _MODELOS_DO_ENV + [m for m in _MODELOS_PADRAO if m not in _MODELOS_DO_...` |

### `backend/app/listar_modelos.py`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [8](../backend/app/listar_modelos.py#L8) | Condicional `if`/`elif` | `if __name__ == "__main__":` |
| [9](../backend/app/listar_modelos.py#L9) | Condicional `if`/`elif` | `if not gemini.configurado():` |
| [11](../backend/app/listar_modelos.py#L11) | Condicional `else` | `else:` |
| [13](../backend/app/listar_modelos.py#L13) | Repetição `for` | `for nome in gemini.listar_modelos():` |
| [14](../backend/app/listar_modelos.py#L14) | Condicional `if`/`elif` | `if "flash" in nome:` |

### `frontend/projeto1/analisar.js`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [12](../frontend/projeto1/analisar.js#L12) | Condicional (ternário `c ? a : b`) | `: (location.protocol === 'file:' \|\| location.port === '5500' \|\| location.port === '5501...` |
| [44](../frontend/projeto1/analisar.js#L44) | Repetição `forEach` | `Object.keys(atributos \|\| {}).forEach(function (nome) {` |
| [45](../frontend/projeto1/analisar.js#L45) | Condicional `if` | `if (nome === 'texto') elemento.textContent = atributos[nome];` |
| [46](../frontend/projeto1/analisar.js#L46) | Condicional `else` | `else elemento.setAttribute(nome, atributos[nome]);` |
| [48](../frontend/projeto1/analisar.js#L48) | Repetição `forEach` | `(filhos \|\| []).forEach(function (filho) {` |
| [49](../frontend/projeto1/analisar.js#L49) | Condicional `if` | `if (filho) elemento.appendChild(typeof filho === 'string' ? document.createTextNode(fil...` |
| [49](../frontend/projeto1/analisar.js#L49) | Condicional (ternário `c ? a : b`) | `if (filho) elemento.appendChild(typeof filho === 'string' ? document.createTextNode(fil...` |
| [62](../frontend/projeto1/analisar.js#L62) | Repetição `forEach` | `abas.forEach(function (outra) {` |
| [65](../frontend/projeto1/analisar.js#L65) | Condicional (ternário `c ? a : b`) | `outra.tabIndex = selecionada ? 0 : -1;` |
| [68](../frontend/projeto1/analisar.js#L68) | Condicional `if` | `if (darFoco) aba.focus();` |
| [72](../frontend/projeto1/analisar.js#L72) | Repetição `forEach` | `abas.forEach(function (aba, indice) {` |
| [76](../frontend/projeto1/analisar.js#L76) | Condicional `if` | `if (evento.key === 'ArrowRight') destino = abas[(indice + 1) % abas.length];` |
| [77](../frontend/projeto1/analisar.js#L77) | Condicional `else if` | `else if (evento.key === 'ArrowLeft') destino = abas[(indice - 1 + abas.length) % abas.l...` |
| [78](../frontend/projeto1/analisar.js#L78) | Condicional `else if` | `else if (evento.key === 'Home') destino = abas[0];` |
| [79](../frontend/projeto1/analisar.js#L79) | Condicional `else if` | `else if (evento.key === 'End') destino = abas[abas.length - 1];` |
| [80](../frontend/projeto1/analisar.js#L80) | Condicional `if` | `if (destino) { evento.preventDefault(); abrirAba(destino, true); }` |
| [84](../frontend/projeto1/analisar.js#L84) | Condicional (ternário `c ? a : b`) | `var abaInicial = location.hash === '#analisar' ? 'aba-mensagem' : lerStorage('alo-segur...` |
| [85](../frontend/projeto1/analisar.js#L85) | Condicional `if` | `if (abaInicial && document.getElementById(abaInicial)) abrirAba(document.getElementById...` |
| [103](../frontend/projeto1/analisar.js#L103) | Condicional (ternário `c ? a : b`) | `return marcado ? marcado.value : 'redes_sociais';` |
| [150](../frontend/projeto1/analisar.js#L150) | Repetição `forEach` | `form.querySelectorAll('input[name="canal"]').forEach(function (opcao) {` |
| [167](../frontend/projeto1/analisar.js#L167) | Condicional (ternário `c ? a : b`) | `var nivel = NIVEIS[dados.nivel] ? dados.nivel : 'medio';` |
| [187](../frontend/projeto1/analisar.js#L187) | Repetição `forEach` | `(dados.taticas_info \|\| []).forEach(function (t) { pesoPorTatica[t.id] = t; });` |
| [190](../frontend/projeto1/analisar.js#L190) | Repetição `forEach` | `dados.red_flags.forEach(function (flag) {` |
| [193](../frontend/projeto1/analisar.js#L193) | Condicional (ternário `c ? a : b`) | `info ? el('span', { 'class': 'etiqueta ' + info.peso, texto: info.nome }) : null,` |
| [194](../frontend/projeto1/analisar.js#L194) | Condicional (ternário `c ? a : b`) | `flag.trecho ? el('div', { 'class': 'flag-trecho', texto: '“' + flag.trecho + '”' }) : n...` |
| [203](../frontend/projeto1/analisar.js#L203) | Condicional (ternário `c ? a : b`) | `var bloco = el('div', {}, [secao(dados.analise_link.length > 1 ? 'Análise dos links' : ...` |
| [204](../frontend/projeto1/analisar.js#L204) | Repetição `forEach` | `dados.analise_link.forEach(function (link) {` |
| [205](../frontend/projeto1/analisar.js#L205) | Condicional (ternário `c ? a : b`) | `var classeTipo = link.tipo === 'legitimo_provavel' ? 'ok' : (link.tipo === 'indetermina...` |
| [207](../frontend/projeto1/analisar.js#L207) | Repetição `forEach` | `(link.motivos \|\| []).forEach(function (motivo) { lista.appendChild(el('li', { texto: mo...` |
| [212](../frontend/projeto1/analisar.js#L212) | Condicional (ternário `c ? a : b`) | `link.dominio_real ? el('span', {}, ['Domínio real: ', el('code', { texto: link.dominio_...` |
| [214](../frontend/projeto1/analisar.js#L214) | Condicional (ternário `c ? a : b`) | `link.motivos && link.motivos.length ? lista : el('p', { 'class': 'observacao', texto: '...` |
| [221](../frontend/projeto1/analisar.js#L221) | Condicional (ternário `c ? a : b`) | `var lista = el(numerada ? 'ol' : 'ul', { 'class': numerada ? 'steps-list' : 'tips-list'...` |
| [222](../frontend/projeto1/analisar.js#L222) | Repetição `forEach` | `itens.forEach(function (texto, i) {` |
| [224](../frontend/projeto1/analisar.js#L224) | Condicional (ternário `c ? a : b`) | `? el('li', {}, [el('span', { 'class': 'n', texto: String(i + 1) }), el('span', { texto:...` |
| [234](../frontend/projeto1/analisar.js#L234) | Condicional `if` | `if (dados.aviso_ajuda) {` |
| [239](../frontend/projeto1/analisar.js#L239) | Condicional `if` | `if (dados.aviso_sistema) {` |
| [247](../frontend/projeto1/analisar.js#L247) | Condicional `if` | `if (rede && canalEscolhido() === 'redes_sociais') {` |
| [251](../frontend/projeto1/analisar.js#L251) | Condicional `if` | `if (dados.golpe_parecido) {` |
| [258](../frontend/projeto1/analisar.js#L258) | Condicional `if` | `if (dados.red_flags && dados.red_flags.length) partes.push(montarRedFlags(dados));` |
| [260](../frontend/projeto1/analisar.js#L260) | Condicional `if` | `if (dados.taticas_info && dados.taticas_info.length) {` |
| [262](../frontend/projeto1/analisar.js#L262) | Repetição `forEach` | `dados.taticas_info.forEach(function (t) {` |
| [268](../frontend/projeto1/analisar.js#L268) | Condicional `if` | `if (dados.dicas && dados.dicas.length) {` |
| [274](../frontend/projeto1/analisar.js#L274) | Condicional `if` | `if (dados.analise_link && dados.analise_link.length) partes.push(montarLinks(dados));` |
| [275](../frontend/projeto1/analisar.js#L275) | Condicional `if` | `if (dados.sinais_de_legitimidade && dados.sinais_de_legitimidade.length) {` |
| [280](../frontend/projeto1/analisar.js#L280) | Condicional (ternário `c ? a : b`) | `: (dados.nivel === 'alto' \|\| dados.nivel === 'muito_alto') ? PASSOS_SE_JA_CAIU : [];` |
| [281](../frontend/projeto1/analisar.js#L281) | Condicional `if` | `if (passos.length) {` |
| [283](../frontend/projeto1/analisar.js#L283) | Repetição `forEach` | `passos.forEach(function (texto, i) {` |
| [287](../frontend/projeto1/analisar.js#L287) | Condicional `if` | `if (dados.se_ja_caiu && dados.se_ja_caiu.length) detalhes.open = true;` |
| [291](../frontend/projeto1/analisar.js#L291) | Condicional `if` | `if (dados.observacoes) partes.push(el('p', { 'class': 'observacao', texto: dados.observ...` |
| [296](../frontend/projeto1/analisar.js#L296) | Condicional `if` | `if (dados.dados_ocultados > 0) {` |
| [297](../frontend/projeto1/analisar.js#L297) | Condicional (ternário `c ? a : b`) | `origem += ' Ocultamos ' + dados.dados_ocultados + (dados.dados_ocultados === 1 ? ' dado...` |
| [301](../frontend/projeto1/analisar.js#L301) | Repetição `forEach` | `partes.forEach(function (parte) { resultado.appendChild(parte); });` |
| [304](../frontend/projeto1/analisar.js#L304) | Condicional `if` | `if (titulo) titulo.focus();` |
| [312](../frontend/projeto1/analisar.js#L312) | Condicional (ternário `c ? a : b`) | `botao.querySelector('span').textContent = ativo ? 'Analisando…' : 'Analisar mensagem';` |
| [319](../frontend/projeto1/analisar.js#L319) | Condicional `if` | `if (texto.length < 3) {` |
| [338](../frontend/projeto1/analisar.js#L338) | Condicional `if` | `if (!resposta.ok) {` |
| [339](../frontend/projeto1/analisar.js#L339) | Condicional (ternário `c ? a : b`) | `var detalhe = typeof corpo.detail === 'string' ? corpo.detail : 'Não foi possível anali...` |

### `frontend/projeto1/proj1.js`

| Linha | Estrutura | Código |
| --- | --- | --- |
| [24](../frontend/projeto1/proj1.js#L24) | Condicional (ternário `c ? a : b`) | `themeToggle.querySelector('span').textContent = dark ? 'Modo claro' : 'Modo escuro';` |
| [25](../frontend/projeto1/proj1.js#L25) | Condicional (ternário `c ? a : b`) | `themeToggle.querySelector('i').className = dark ? 'ti ti-sun' : 'ti ti-moon';` |
| [38](../frontend/projeto1/proj1.js#L38) | Condicional (ternário `c ? a : b`) | `applyTheme(savedTheme === 'light' ? 'light' : 'dark');` |
| [40](../frontend/projeto1/proj1.js#L40) | Condicional (ternário `c ? a : b`) | `themeToggle.addEventListener('click', function () { applyTheme(document.documentElement...` |
| [41](../frontend/projeto1/proj1.js#L41) | Condicional `if` | `decreaseFont.addEventListener('click', function () { if (fontSize > 1) applyFontSize(fo...` |
| [42](../frontend/projeto1/proj1.js#L42) | Condicional `if` | `increaseFont.addEventListener('click', function () { if (fontSize < 5) applyFontSize(fo...` |
| [70](../frontend/projeto1/proj1.js#L70) | Condicional `if` | `if ((d.length === 12 \|\| d.length === 13) && d.indexOf('55') === 0) d = d.slice(2);` |
| [75](../frontend/projeto1/proj1.js#L75) | Repetição `forEach` | `[step1, step2].forEach(function (s) {` |
| [110](../frontend/projeto1/proj1.js#L110) | Repetição `forEach` | `['f-nome', 'f-email', 'f-telefone'].forEach(function (id) {` |
| [122](../frontend/projeto1/proj1.js#L122) | Condicional `if` | `if (emailAchados) achados = achados.concat(emailAchados);` |
| [123](../frontend/projeto1/proj1.js#L123) | Condicional `if` | `if (telAchados) achados = achados.concat(telAchados);` |
| [130](../frontend/projeto1/proj1.js#L130) | Condicional (ternário `c ? a : b`) | `'<h2>Encontramos ' + achados.length + (achados.length === 1 ? ' exposição' : ' exposiçõ...` |
| [133](../frontend/projeto1/proj1.js#L133) | Repetição `forEach` | `achados.forEach(function (a) {` |
| [168](../frontend/projeto1/proj1.js#L168) | Condicional `if` | `if (!validate()) {` |
| [170](../frontend/projeto1/proj1.js#L170) | Condicional `if` | `if (primeiroInvalido) primeiroInvalido.focus();` |
| [197](../frontend/projeto1/proj1.js#L197) | Condicional `if` | `if (achados.length > 0) {` |
| [199](../frontend/projeto1/proj1.js#L199) | Condicional `else` | `} else {` |
| [204](../frontend/projeto1/proj1.js#L204) | Condicional `if` | `if (titulo) { titulo.setAttribute('tabindex', '-1'); titulo.focus(); }` |
| [217](../frontend/projeto1/proj1.js#L217) | Repetição `forEach` | `['f-nome', 'f-email', 'f-telefone'].forEach(function (id) {` |
