# Aprendizado contínuo: como o agente fica mais esperto com casos reais

## O que "se auto-treinar" significa neste projeto

Existem dois jeitos de fazer uma IA aprender com casos novos:

| | Retreinar o modelo (*fine-tuning*) | Memória de casos + base viva (o nosso) |
|---|---|---|
| O que muda | Os "neurônios" do modelo | O conhecimento que entregamos ao modelo a cada análise |
| Precisa de | Milhares de exemplos rotulados, tempo de treino, custo | Um banco de dados e boa curadoria |
| Quando aprende | Só quando alguém roda um novo treino | **Na hora**: um caso aprovado já vale na próxima análise |
| Funciona com a API gratuita do Gemini | Não, na prática | **Sim** |
| Dá para explicar o que aprendeu | Difícil | Fácil: dá para mostrar quais casos foram usados |

Por isso o agente **não altera o Gemini**. Ele aprende como um analista humano: guarda os casos
que viu, consulta os casos parecidos antes de cada análise e atualiza a lista de golpes conhecidos
quando aparece um golpe novo. Essa técnica se chama **RAG com exemplos dinâmicos** (*retrieval-
augmented generation*) e é usada em sistemas reais de detecção de fraude.

## O ciclo completo

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
 │ 1. Usuário   │──▶│ 2. Agente    │──▶│ 3. Usuário   │──▶│ 4. Anonimização  │
 │ cola mensagem│   │ analisa      │   │ dá feedback  │   │ (tira CPF, fone…)│
 └──────────────┘   └──────▲───────┘   └──────────────┘   └────────┬─────────┘
                           │                                       ▼
 ┌──────────────┐   ┌──────┴───────┐   ┌──────────────┐   ┌──────────────────┐
 │ 8. Golpe novo│◀──│ 7. Busca     │◀──│ 6. Memória   │◀──│ 5. Curadoria     │
 │ vira item da │   │ casos        │   │ de casos     │   │ (moderador       │
 │ base         │   │ parecidos    │   │ confirmados  │   │ aprova no CRUD)  │
 └──────────────┘   └──────────────┘   └──────────────┘   └──────────────────┘
                     9. Métricas acompanham se o agente está acertando mais
```

## Passo 1 e 2: cada análise fica registrada

Toda análise é salva (já anonimizada, ver passo 4) para poder receber feedback depois.

```json
{
  "id": "an_000123",
  "data": "2026-11-18T14:32:00",
  "plataforma": "whatsapp",
  "texto_anonimizado": "Oi mãe, esse é meu número novo... Pix de 1.850 para [CHAVE_PIX]",
  "resultado": {
    "probabilidade_golpe": 92,
    "nivel": "muito_alto",
    "taticas_detectadas": ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro"],
    "golpe_parecido": "wa001",
    "possivel_golpe_novo": false
  },
  "casos_usados": ["caso_0042", "caso_0107"],
  "versao_prompt": "2.0",
  "consentimento_aprendizado": true
}
```

## Passo 3: feedback do usuário

Depois do resultado, a página pergunta: **"Você confirmou se era golpe?"**

- ✅ **Era golpe** → opcional: "O que aconteceu?" (texto curto) e "Você chegou a perder algo?"
- ❌ **Não era golpe** → opcional: "Como você confirmou?"
- 🤷 **Ainda não sei**: a página pode perguntar de novo depois

Só entra no aprendizado quem marcar a caixa:
*"Autorizo usar esta mensagem, sem meus dados pessoais, para melhorar o detector."*

## Passo 4: anonimização (obrigatória, por causa da LGPD)

Antes de salvar qualquer texto, o código troca dados pessoais por marcadores:

| Dado | Exemplo | Vira |
|---|---|---|
| Telefone | (81) 99876-5432, +55 81 998765432 | `[TELEFONE]` |
| CPF | 123.456.789-00 | `[CPF]` |
| CNPJ | 12.345.678/0001-90 | `[CNPJ]` |
| Email | maria@gmail.com | `[EMAIL]` |
| Cartão | 4111 1111 1111 1111 | `[CARTAO]` |
| Chave Pix aleatória | 7d9f...-...-... (formato UUID) | `[CHAVE_PIX]` |
| Agência e conta | ag 1234 cc 56789-0 | `[CONTA]` |
| @ de usuário | @fulano.silva | `[USUARIO]` |

**Mantemos** o que ajuda a reconhecer o golpe: valores ("R$ 1.850"), **domínios de links**
(`itau-protecao-cliente.com`) e o texto da abordagem. Nomes de pessoas são difíceis de detectar
automaticamente: o moderador revisa no passo 5. Casos que não forem confirmados em até **90 dias**
são apagados.

## Passo 5: curadoria (o filtro contra erros e sabotagem)

Feedback de usuário não vira conhecimento direto, porque alguém poderia marcar golpes como
"seguros" de propósito (*envenenamento de dados*). As regras são:

1. **Toda divergência vai para revisão humana:** o agente deu 90 e o usuário disse "não era golpe",
   ou o contrário. Esses são os casos mais valiosos, porque mostram onde o agente erra.
2. **Aprovação automática** só quando **três ou mais** feedbacks independentes concordam entre si
   **e** com o agente, numa nota claramente alta (≥ 80) ou claramente baixa (≤ 15).
3. Fora isso, o caso vai para a **fila de moderação**, uma tela do CRUD que vocês já têm, onde um
   membro da equipe:
   - confere se a anonimização ficou boa (e remove nomes);
   - marca `golpe` ou `nao_golpe`;
   - corrige as táticas, se necessário;
   - escreve uma lição curta ("Golpista usou o nome real da escola do filho").

Formato de um caso confirmado:

```json
{
  "id": "caso_0107",
  "plataforma": "whatsapp",
  "texto": "Oi mãe, esse é meu número novo... Pix de 1.850 para [CHAVE_PIX]",
  "rotulo": "golpe",
  "taticas": ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro", "urgencia"],
  "golpe_base": "wa001",
  "licao": "Golpista citou um boleto com horário limite para criar pressa.",
  "nota_do_agente_na_epoca": 92,
  "confirmado_por": "moderador",
  "data_confirmacao": "2026-11-20",
  "reservado_para_teste": false
}
```

## Passo 6 e 7: usar os casos na próxima análise

Antes de chamar o Gemini, o código procura os **casos confirmados mais parecidos** com a mensagem
nova e os coloca no lugar de `{{CASOS_SIMILARES}}` no prompt.

### Fase 1: busca simples, sem custo (dá para fazer já)

1. Uma primeira análise rápida no próprio código, ou uma primeira chamada barata ao Gemini, levanta
   as táticas da mensagem nova.
2. Para cada caso confirmado **da mesma plataforma**, calcula-se a semelhança:
   - **táticas em comum**: quantas táticas os dois têm em comum ÷ total de táticas diferentes dos
     dois (índice de Jaccard);
   - **palavras em comum**: o mesmo cálculo com as palavras importantes, sem "de", "o", "que" etc.;
   - `semelhança = 0,6 × táticas + 0,4 × palavras`.
3. Ficam os 5 casos com semelhança ≥ 0,3, tentando incluir **pelo menos 1 caso `nao_golpe`**
   (para o agente não achar que tudo é golpe).

Em pseudocódigo (aqui aparecem as estruturas de repetição e condicionais que vocês vão mostrar):

```
melhores = []
PARA CADA caso EM casos_confirmados:
    SE caso.plataforma == plataforma E caso.reservado_para_teste == falso:
        s = 0.6 * jaccard(caso.taticas, taticas_novas) + 0.4 * jaccard(palavras(caso.texto), palavras_novas)
        SE s >= 0.3:
            adicionar (caso, s) em melhores
ordenar melhores por s, do maior para o menor
pegar os 5 primeiros
SE nenhum dos 5 for "nao_golpe" E existir algum "nao_golpe" em melhores:
    trocar o 5º pelo melhor "nao_golpe"
```

### Fase 2: busca por significado (mais precisa)

Usar a API de **embeddings** do Gemini, que transforma o texto em uma lista de números que
representam o significado, e comparar com a similaridade do cosseno. Ela encontra golpes parecidos
mesmo com palavras diferentes ("caiu meu celular na água" ≈ "perdi meu chip").

### Como os casos entram no prompt

```
<caso id="caso_0107" rotulo="golpe" golpe_base="wa001" semelhanca="0.82">
Texto: Oi mãe, esse é meu número novo... Pix de 1.850 para [CHAVE_PIX]
Táticas: personificacao_conhecido, troca_de_canal, pedido_de_dinheiro, urgencia
Lição: Golpista citou um boleto com horário limite para criar pressa.
</caso>
```

Limites: no máximo 5 casos, cada texto cortado em 500 caracteres. Isso protege o limite de tokens
do plano gratuito.

## Passo 8: golpes novos viram itens da base

Quando o agente devolve `possivel_golpe_novo: true` (nota ≥ 60 e nada parecido na base), o caso vai
para a lista de **candidatos a golpe novo**. Quando houver **três ou mais candidatos parecidos**
entre si:

1. O moderador agrupa os candidatos e roda o prompt [prompt_novo_golpe.md](prompt_novo_golpe.md),
   que escreve um rascunho do golpe no mesmo formato da base (nome, resumo, tags, táticas, sinais e
   dicas).
2. O moderador revisa, ajusta e aprova.
3. O golpe entra no arquivo da plataforma (ou na tabela do banco) com o próximo id
   (ex.: `wa106`), e a versão da base sobe.

Assim a base continua atualizada com golpes que ainda nem saíram nas notícias.

## Passo 9: provar que o agente está melhorando

Separar **20% dos casos confirmados** como *conjunto de teste* (`reservado_para_teste: true`).
Esses casos nunca entram no prompt; servem para medir o agente, como uma prova cujas respostas ele
não viu. Uma vez por semana, ou a cada mudança no prompt:

| Métrica | O que mostra | Meta |
|---|---|---|
| **Falsos negativos** (golpe com nota < 46) | Golpes que o agente deixou passar: **o erro mais grave** | O menor possível |
| Falsos positivos (não golpe com nota ≥ 46) | Alarmes à toa | Baixo |
| Acerto geral | % de casos em que o nível bate com o rótulo | Subir mês a mês |
| Calibração | Dos casos com nota 80–99, quantos eram golpe mesmo? | ~80% ou mais |

Se a calibração estiver errada (ex.: casos com nota "alto" eram golpe só 30% das vezes), ajustem
os **pesos** em `taxonomia.json` e na seção 6 do prompt e meçam de novo. Esse gráfico de evolução
é ótimo para a apresentação.

## Cuidados

- **Injeção de instruções:** um caso salvo pode conter "ignore suas regras". Por isso os casos vão
  dentro de `<caso>…</caso>`, e o prompt diz que são dados, não ordens.
- **Envenenamento:** curadoria humana e a regra dos três feedbacks.
- **Privacidade:** anonimização antes de salvar, consentimento explícito e prazo de 90 dias.
- **Plano gratuito:** limite de 5 casos e textos cortados.
- **Transparência:** a resposta pode mostrar ao usuário "Esta análise considerou 3 casos
  parecidos já confirmados pela equipe".

## O que vamos precisar no código (quando você mandar o projeto)

- [ ] Tabelas ou coleções: `analises`, `feedbacks`, `casos_confirmados`, `candidatos_golpe_novo`
- [ ] Função de anonimização (expressões regulares da tabela do passo 4)
- [ ] Botões de feedback e caixa de consentimento na página
- [ ] Tela de moderação no CRUD (listar, aprovar, rejeitar e editar casos)
- [ ] Função de busca de casos similares (Fase 1)
- [ ] Montagem do prompt trocando os marcadores `{{...}}`
- [ ] Relatório de métricas com o conjunto de teste
