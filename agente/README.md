# Agentes do Alô Seguro

A pasta tem três agentes que usam o Gemini:

- **Detector de Golpes** (`prompt_sistema.md`): analisa mensagens e links (`POST /api/analisar`).
- **Orientador de Vazamentos** (`prompt_vazamento.md`): explica o resultado da verificação de
  vazamentos (`POST /api/v1/check`) e ordena as recomendações. Recebe **só metadados** (nome e data
  do incidente, tipos de dado expostos), nunca o e-mail ou o telefone, e só pode escolher
  recomendações do catálogo fixo em `backend/app/vazamentos.py`; não cria textos de ação nem links.
  Se a IA falhar, as regras do backend fazem o resumo e a ordem.
- **Conversa Segura** (`prompt_conversa.md`): chat "Tirar dúvidas" (`POST /api/v1/conversa`).
  Reaproveita as seções 3 e 4 do `prompt_sistema.md` (o conhecimento fica num lugar só). Responde em
  até 120 palavras, uma pergunta por vez, e não pode escrever links nem telefones: o backend
  (`backend/app/conversa.py`) apaga o que não for `.gov.br` e responde por regras se a IA falhar.

O restante deste documento trata do Detector de Golpes.

## Arquivos

```
agente/
├── prompt_sistema.md        ← instrução principal enviada ao Gemini (v2)
├── prompt_vazamento.md      ← instrução do Orientador de Vazamentos (resultado da consulta)
├── prompt_conversa.md       ← instrução do chat "Tirar dúvidas" (Conversa Segura)
├── prompt_novo_golpe.md     ← prompt do moderador para criar golpes novos a partir de casos reais
├── aprendizado_continuo.md  ← como o agente aprende com os casos reais do projeto
├── taxonomia.json           ← definição de todas as tags (classificação + 25 táticas)
├── INTEGRACAO_CRUD.md       ← o que o CRUD precisa guardar para o agente aprender
├── casos_reais/
│   └── casos_confirmados.json  ← casos reais aprovados (fonte provisória até o CRUD existir)
└── base_golpes/
    ├── whatsapp.json   (105 golpes)
    ├── instagram.json  (102 golpes)
    ├── snapchat.json   (101 golpes)
    ├── discord.json    (101 golpes)
    ├── email.json      (102 golpes)
    └── links.json      (102 tipos de link fraudulento)
                         Total: 613
```

## Como as bases são usadas

A tela oferece três opções. **Mensagem de rede social** junta as bases de WhatsApp, Instagram,
Snapchat e Discord (409 golpes) num formato enxuto, e a IA descobre a rede pelo texto, inclusive
Facebook, LinkedIn, Telegram, TikTok e SMS, que têm perfil próprio no prompt. **E-mail** usa
`email.json` e **Link** usa `links.json`.

## Formato de cada golpe

```json
{
  "id": "wa001",
  "nome": "Golpe do número novo",
  "resumo": "O que é o golpe, em uma frase.",
  "tags": ["comum", "conhecido", "dano_financeiro_alto", "dano_emocional_alto"],
  "taticas": ["personificacao_conhecido", "troca_de_canal", "pedido_de_dinheiro", "urgencia", "evita_verificacao", "falta_de_dados"],
  "sinais": ["red flags típicas"],
  "dicas": ["como confirmar ou se proteger"]
}
```

## Dois tipos de tag

**1. Tags de classificação (`tags`):** dizem *que tipo de golpe é*.

| Tag | Significado |
|---|---|
| `comum` | Aparece com frequência hoje nesse canal |
| `novo` | Surgiu ou cresceu entre 2025 e 2026 |
| `conhecido` | Golpe clássico, muito divulgado |
| `dano_financeiro_alto` | Costuma gerar perda grande de dinheiro |
| `dano_emocional_alto` | Causa medo, vergonha, culpa ou trauma |

**2. Tags de tática (`taticas`):** dizem *como o golpista manipula*. São as red flags que o agente
procura na mensagem. Cada uma tem um peso na nota (detalhes em `taxonomia.json` e na seção 6 do prompt).

| Peso | Táticas |
|---|---|
| **Forte (+25)** | `pedido_de_codigo`, `acesso_remoto`, `arquivo_malicioso`, `pagamento_antecipado`, `recebedor_divergente` |
| **Média (+15)** | `pedido_de_dinheiro`, `pedido_de_dados`, `personificacao_conhecido`, `personificacao_instituicao`, `troca_de_canal`, `link_suspeito`, `promessa_irreal`, `ameaca_medo`, `evita_verificacao`, `sigilo`, `documento_falso`, `uso_de_ia`, `conteudo_intimo` |
| **Fraca (+10)** | `urgencia`, `falta_de_dados`, `apelo_emocional`, `contato_nao_solicitado`, `prova_social_falsa`, `isca_inicial`, `linguagem_estranha` |

As fracas valem pouco **sozinhas** (urgência em "corre que o ônibus vai sair" não é golpe), mas
viram alerta grave quando aparecem junto de um pedido. Por isso o prompt tem **pisos por
combinação**: por exemplo, conhecido + número novo + pedido de dinheiro dá no mínimo 88%.

### Táticas mais frequentes nos 613 golpes

| Tática | Golpes |
|---|---|
| Promessa boa demais | 266 |
| Pagamento antecipado | 181 |
| Se passa por instituição | 166 |
| Pedido de dados | 160 |
| Link suspeito | 158 |
| Urgência | 114 |
| Recebedor divergente | 81 |
| Ameaça ou medo | 78 |

`falta_de_dados` e `linguagem_estranha` aparecem pouco na base porque dependem do texto de cada
mensagem, não do tipo de golpe. O agente procura essas duas táticas em toda análise.

## Como o prompt funciona (resumo)

1. **Contexto 2025–2026** com os dados da pesquisa (Febraban, FBSP/Datafolha, Serasa, FBI).
2. **Engenharia social:** disfarce, gatilho emocional, isolamento e pedido.
3. **Regras de ouro:** o que bancos, governo, plataformas e empresas nunca fazem.
4. **Perfil de cada canal:** como abordam, golpes dominantes, público atingido, sinais típicos.
5. **25 táticas com pesos**, pisos por combinação, atenuantes e limite de 1 a 99%.
6. **Roteiro técnico para links** (domínio real, letras trocadas, encurtadores, hospedagem genérica…).
7. **Regras para red flags e dicas** específicas, mais passos de socorro para quem já caiu.
8. **Situações especiais e segurança** (menores, risco à vida, injeção de instruções).
9. **Casos reais aprendidos** (`{{CASOS_SIMILARES}}`) + **base da plataforma** (`{{BASE_DE_GOLPES}}`).
10. **Seis exemplos resolvidos** e o **formato JSON** da resposta.

## Manutenção

- Ao mudar pesos ou táticas, atualize **as duas coisas**: `taxonomia.json` e a seção 6 do prompt.
- Golpes novos entram pelo fluxo de `aprendizado_continuo.md`, com revisão humana.
- Revisem a base a cada semestre.

## Limitações (importante para a apresentação)

- As tags de frequência e dano são uma **classificação qualitativa**, feita a partir de reportagens,
  alertas e relatórios de 2025–2026. Não são estatística oficial; a tag `comum` foi usada de forma ampla.
- As táticas de cada golpe foram atribuídas manualmente e podem ser refinadas com os casos reais.
- O agente dá uma **estimativa** e não substitui a confirmação por outro canal.
