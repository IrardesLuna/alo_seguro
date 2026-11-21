# Alô Seguro

> **Consulte se seus dados pessoais aparecem em vazamentos conhecidos e receba orientações claras para se proteger.**

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-DAA520?style=for-the-badge)](#status-do-projeto)
[![Projeto acadêmico](https://img.shields.io/badge/CESAR%20School-Projetos%201-0A66C2?style=for-the-badge)](#sobre-o-projeto)

O **Alô Seguro** é um projeto acadêmico do **Grupo 5 (Squad 05)**, desenvolvido na disciplina **Projetos 1**, da CESAR School, no semestre **2026.2**. A proposta é tornar a consulta sobre exposição de dados mais simples, compreensível e segura — especialmente para pessoas que não sabem como reagir após um possível vazamento.

> **Aviso:** o projeto está em desenvolvimento. O escopo, as fontes de consulta e os recursos descritos como planejados podem mudar durante a implementação.

---

## Índice

- [Sobre o projeto](#sobre-o-projeto)

- [Problema e proposta de valor](#problema-e-proposta-de-valor)

- [Público e objetivos](#p%C3%BAblico-e-objetivos)

- [Como a experiência deve funcionar](#como-a-experi%C3%AAncia-deve-funcionar)

- [Privacidade e segurança](#privacidade-e-seguran%C3%A7a)

- [Tecnologias](#tecnologias)

- [Arquitetura e escalabilidade](#arquitetura-e-escalabilidade)

- [Experiência visual e animações](#experi%C3%AAncia-visual-e-anima%C3%A7%C3%B5es)

- [Estrutura sugerida do projeto](#estrutura-sugerida-do-projeto)

- [Começando](#come%C3%A7ando)

- [Roadmap](#roadmap)

- [Equipe](#equipe)

- [Contribuição](#contribui%C3%A7%C3%A3o)

- [Licença](#licen%C3%A7a)

## Sobre o projeto

Muitas pessoas não sabem se seus dados pessoais já apareceram em vazamentos. Quando suspeitam que foram afetadas, podem não saber quais medidas tomar ou onde buscar ajuda. Ao mesmo tempo, serviços falsos de “verificação” podem explorar essa preocupação para solicitar senhas, dados bancários ou informações desnecessárias.

O Alô Seguro propõe uma experiência de consulta que explica o resultado em linguagem acessível e orienta a pessoa sobre próximos passos. A ideia é que a plataforma informe **quais dados foram identificados, em quais incidentes e quando**, sempre que essa informação estiver disponível nas fontes utilizadas.

### Problema e proposta de valor

- **Problema:** falta de informação acessível e de orientação prática diante de possíveis exposições de dados.

- **Proposta:** reunir uma consulta objetiva e recomendações de segurança em uma interface fácil de entender.

- **Princípio central:** ajudar sem aumentar o risco para quem consulta. O serviço não deve solicitar senhas, números de cartão ou credenciais bancárias.

### Público e objetivos

A solução é pensada para pessoas que desejam verificar a exposição de um e-mail ou telefone e precisam de instruções claras para agir. O produto deve priorizar:

- linguagem simples, sem exigir conhecimento técnico;

- indicação clara do que foi ou não encontrado;

- recomendações acionáveis e proporcionais ao resultado;

- transparência sobre limites, fontes e atualidade das informações;

- acessibilidade em dispositivos móveis e para diferentes necessidades de uso.

## Como a experiência deve funcionar

Fluxo conceitual da consulta:

1. A pessoa informa os dados estritamente necessários para a consulta, inicialmente nome, e-mail e/ou telefone, conforme o escopo definido pelo produto.

1. A interface explica o propósito da consulta e como os dados serão tratados antes do envio.

1. O sistema consulta as fontes de dados autorizadas e disponíveis.

1. O resultado apresenta o status da consulta e, quando houver correspondência, os dados expostos, a fonte e a data do incidente — sem revelar informações sensíveis além do necessário.

1. A pessoa recebe recomendações contextualizadas, como alterar senhas reutilizadas, ativar autenticação em dois fatores e entrar em contato com instituições relevantes quando houver risco financeiro.

As recomendações sobre registro de ocorrência ou comunicação a órgãos competentes devem ser contextualizadas e acompanhadas de links para canais oficiais atualizados. O Alô Seguro é uma ferramenta informativa; não substitui orientação jurídica, atendimento bancário ou resposta oficial a incidentes.

## Privacidade e segurança

A privacidade deve orientar tanto a interface quanto a implementação. A intenção do projeto é **não armazenar os dados consultados** e **nunca solicitar senhas, cartões ou dados bancários**. Essa promessa só deve ser publicada como garantia após ser confirmada pelo comportamento real do sistema, incluindo logs, banco de dados, serviços externos e ambiente de hospedagem.

Diretrizes para implementação e evolução:

- coletar apenas os campos indispensáveis para a consulta;

- explicar finalidade, processamento, retenção e compartilhamento antes do envio;

- evitar gravar dados pessoais em logs, métricas, mensagens de erro ou ferramentas de analytics;

- proteger o tráfego com HTTPS em produção e validar entradas no servidor;

- limitar tentativas e aplicar controles contra abuso, enumeração e automação maliciosa;

- manter dependências e serviços atualizados, com segredos fora do código-fonte;

- documentar fontes consultadas, limitações e procedimentos para incidentes;

- avaliar requisitos legais e de proteção de dados aplicáveis antes de disponibilizar o serviço publicamente.

> **Importante:** a disponibilidade e a precisão dos resultados dependem das fontes integradas. Uma consulta sem correspondências não comprova que os dados nunca foram expostos.

## Tecnologias

Tecnologias informadas para a base atual do projeto:

| Camada | Tecnologia | Uso previsto |
| --- | --- | --- |
| Front-end | HTML, CSS e JavaScript | Interface e interação no navegador |
| Back-end | Python + FastAPI | API e processamento das consultas |
| Persistência | SQLite (`sqlite3`) | Persistência local durante o desenvolvimento, se necessária |

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

A escolha de SQLite é adequada para prototipação e desenvolvimento local. Se a aplicação passar a atender múltiplas instâncias ou maior volume de acessos, a camada de persistência deverá ser reavaliada. A arquitetura deve evitar dependência direta entre regras de negócio e um banco específico, facilitando uma eventual migração.

## Arquitetura e escalabilidade

A arquitetura pode começar simples e evoluir por etapas, preservando limites claros entre interface, API, regras de negócio e integrações externas.

### Separação de responsabilidades

- **Interface:** coleta consentida dos campos necessários, validação para usabilidade e apresentação acessível do resultado.

- **API:** validação definitiva dos dados, controle de requisições, respostas padronizadas e tratamento de erros.

- **Serviço de consulta:** concentra as regras de negócio e coordena a consulta às fontes disponíveis.

- **Adaptadores de fontes:** encapsulam cada provedor ou base consultada, evitando acoplamento da aplicação a um único fornecedor.

- **Persistência opcional:** armazena apenas o que for indispensável e permitido pela política definida; não deve ser introduzida por conveniência sem avaliação de privacidade.

### Práticas que facilitam o crescimento

1. **Contratos de API estáveis:** documentar entradas, respostas, erros e versões. O FastAPI pode gerar documentação OpenAPI a partir das rotas.

1. **Integrações substituíveis:** usar uma interface comum para fontes de consulta e tratar indisponibilidade, limites e respostas inconsistentes.

1. **Configuração por ambiente:** separar desenvolvimento, testes e produção; guardar chaves e credenciais em variáveis de ambiente ou serviço de segredos.

1. **Operação resiliente:** definir timeouts, limites de requisição, tratamento de falhas e mensagens que não exponham dados pessoais.

1. **Qualidade verificável:** manter testes para validação, regras de negócio, API e integrações simuladas.

1. **Escala gradual:** medir gargalos antes de adicionar infraestrutura. Se necessário, avaliar banco de dados gerenciado, cache ou processamento assíncrono sem armazenar dados pessoais além do estritamente necessário.

1. **Observabilidade com privacidade:** acompanhar disponibilidade e erros agregados sem registrar os valores consultados.

### Rotas da API

Documentação interativa (OpenAPI) em **http://127.0.0.1:8000/docs** com o servidor ligado.

| Método | Caminho | Finalidade |
| --- | --- | --- |
| `GET` | `/health` | Disponibilidade do serviço e modo da consulta de vazamentos (demonstração ou real) |
| `POST` | `/api/v1/check` | Verifica e-mail e/ou telefone em vazamentos conhecidos e devolve recomendações |
| `POST` | `/api/analisar` | Analisa uma mensagem ou link e estima a chance de ser golpe |
| `POST` | `/api/v1/conversa` | Chat para tirar dúvidas sobre golpes e phishing (o histórico vem do navegador; nada é guardado) |
| `GET` `POST` `PATCH` `DELETE` | `/api/v1/admin/casos` | CRUD dos casos reais (só aceita pedidos do próprio computador) |
| `GET` | `/api/plataformas` | Opções da tela de análise e quantos golpes há em cada base |
| `GET` | `/api/saude` | Estado da IA (Gemini) |

Exemplo de pedido para `/api/v1/check` (basta um dos dois campos; nome, senha ou cartão nunca são pedidos):

```json
{ "email": "teste@exemplo.com", "telefone": "(11) 99999-9999" }
```

A resposta traz `status` (`exposto`, `nada_encontrado` ou `nao_verificado`), `resumo`,
`exposicoes` (incidente, data, dados expostos e por qual campo foi encontrado),
`recomendacoes` (com links para canais oficiais), `campos_verificados`, `campos_nao_verificados`,
`fontes`, `demonstracao` e `aviso_limites`. **O e-mail e o telefone consultados não voltam na
resposta, não são guardados nem registrados em log.** As rotas `POST` têm limite de pedidos
por minuto por IP (`LIMITE_POR_MINUTO`), o que também dificulta a enumeração em massa.

Autenticação, consentimento, retenção e requisitos das fontes ainda precisam ser revistos antes de uma publicação real.

## Experiência visual e animações

A interface pode transmitir segurança por meio de hierarquia visual clara, contraste adequado, textos objetivos e estados de carregamento honestos. Uma direção visual possível inclui cores sóbrias, indicadores de status compreensíveis e chamadas para ação que priorizem a proteção do usuário.

Animações podem melhorar a compreensão sem distrair ou sugerir uma certeza que o sistema não possui. Ideias para implementação futura:

- transição curta entre formulário, carregamento e resultado;

- indicador de progresso discreto durante a consulta;

- destaque suave para a seção de recomendações após a resposta;

- microinterações em botões e campos para confirmar ações e validações;

- opção de respeitar `prefers-reduced-motion`, reduzindo ou removendo movimentos para quem preferir.

Animações não devem atrasar a consulta, esconder avisos, piscar de forma agressiva ou usar sinais alarmistas. O estado de carregamento não deve afirmar que uma fonte foi consultada até que isso tenha ocorrido.

## Estrutura sugerida do projeto

A estrutura abaixo é uma sugestão para quando o projeto crescer; ajuste-a para corresponder aos arquivos reais do repositório.

```
alo_seguro/
├── frontend/
│   ├── index.html
│   ├── assets/
│   ├── styles/
│   └── scripts/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── integrations/
│   │   └── schemas/
│   └── tests/
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Começando

### Como rodar localmente

O site e a API rodam juntos pelo FastAPI. Requisitos: **Python 3.12** ou mais novo.

**1. Criar o ambiente virtual e instalar as dependências** (só na primeira vez), no PowerShell,
na **raiz** do repositório:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy backend\.env.example backend\.env
```

Se o PowerShell bloquear o `Activate.ps1` ("a execução de scripts foi desabilitada"), libere
só para o seu usuário e tente de novo:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

No Prompt de Comando (cmd) use `.venv\Scripts\activate.bat`; no Git Bash, Linux ou macOS,
`source .venv/Scripts/activate` (Windows) ou `source .venv/bin/activate` (Linux/macOS).
Com o ambiente ativo, aparece `(.venv)` no começo da linha. Para sair, digite `deactivate`.

**2. Configurar a chave da IA (opcional).** Abra `backend/.env` e cole sua chave gratuita do Gemini em `GEMINI_API_KEY`
(gere em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)). Sem a chave, a análise
de mensagens funciona só com as regras automáticas. A verificação de vazamentos usa por padrão a base de
demonstração (veja [Verificação de vazamentos](#verifica%C3%A7%C3%A3o-de-vazamentos)).

**3. Ligar o servidor** (nas próximas vezes, comece daqui: ative o ambiente e rode):

```powershell
.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000** no navegador. Para parar o servidor, aperte `Ctrl + C`.

Outros comandos úteis (com o ambiente ativo, dentro de `backend`):

| Comando | Para quê |
| --- | --- |
| `python -m pytest` | roda os testes automáticos |
| `python -m app.listar_modelos` | mostra os modelos do Gemini liberados para a sua chave |

A pasta `.venv` e o arquivo `backend/.env` ficam fora do Git (`.gitignore`): cada pessoa cria os seus.
Ao adicionar uma biblioteca nova, coloque-a com a versão em `requirements.txt`, na raiz.

### Verificação de vazamentos

A aba **Verificar vazamento** envia o e-mail e/ou telefone para `POST /api/v1/check`. O nome é
opcional e **não sai do navegador** (serve só para personalizar o resultado). O servidor consulta as
fontes configuradas em `backend/.env`:

| `FONTE_VAZAMENTOS` | O que acontece |
| --- | --- |
| `demo` (padrão) | base local com dados **fictícios**, sem internet. Teste com `teste@exemplo.com` ou `(11) 99999-9999` |
| `hibp` | [Have I Been Pwned](https://haveibeenpwned.com/API/v3) para **e-mail**. Exige chave paga em `HIBP_API_KEY`. O HIBP não verifica telefone: a tela avisa que o telefone não foi verificado |

Cada fonte é um adaptador em `backend/app/fontes.py`; para somar uma fonte nova, basta criar outra
classe com o mesmo método `consultar()`. Incidentes marcados como sensíveis pela fonte aparecem sem o nome.

As recomendações vêm de um catálogo fixo, revisado pela equipe (`backend/app/vazamentos.py`), e são
escolhidas pelos tipos de dado expostos (senha, cartão, documento, telefone…). Se houver chave do
Gemini e `IA_NO_VAZAMENTO=true`, o **Orientador de Vazamentos** (`agente/prompt_vazamento.md`) escreve
o resumo e ordena as recomendações. A IA recebe só o nome e a data dos incidentes e os tipos de dado,
**nunca o e-mail ou o telefone**, e não pode criar recomendações nem links novos. Sem IA, as regras
fazem o mesmo trabalho.

### Análise de mensagens e links

A aba **Analisar mensagem** pergunta "O que você quer analisar?" e oferece três opções:
**mensagem de rede social** (WhatsApp, Instagram, Facebook, LinkedIn, Telegram, TikTok, SMS e outras;
a IA descobre a rede pelo texto), **e-mail** ou **link**. Ela devolve a chance de ser golpe (sempre
entre 1% e 99%), as red flags, as táticas de manipulação e dicas para confirmar. Os arquivos principais:

| Pasta / arquivo | Conteúdo |
| --- | --- |
| `agente/` | base com 613 golpes, taxonomia de táticas e prompts da IA (golpes e vazamentos) |
| `backend/app/main.py` | rotas da API (`/health`, `/api/v1/check`, `/api/analisar`, `/api/plataformas`, `/api/saude`) |
| `backend/app/vazamentos.py` e `fontes.py` | verificação de vazamentos, fontes e recomendações |
| `backend/app/conversa.py` | chat "Tirar dúvidas" |
| `backend/app/casos.py` | CRUD dos casos reais (SQLite) |
| `backend/app/heuristica.py` | regras automáticas (funcionam sem IA) |
| `backend/app/links.py` | análise técnica de links |
| `backend/app/anonimizar.py` | oculta dados pessoais antes de enviar para a IA |
| `frontend/projeto1/proj1.html`, `proj1.js` e `proj1.css` | página e tela de verificação de vazamentos |
| `frontend/projeto1/analisar.js` e `analisar.css` | tela da análise |
| `frontend/projeto1/conversa.js` e `conversa.css` | tela do chat |
| `frontend/projeto1/admin.html`, `admin.js` e `admin.css` | página de moderação dos casos |

O texto colado **não é guardado**. A chave da IA fica só no servidor (`backend/.env`, ignorado pelo Git).

### Tirar dúvidas (chat)

A aba **Tirar dúvidas** é uma conversa guiada para quem tem pouca familiaridade digital: a pessoa
escreve do seu jeito ou toca em perguntas prontas ("Já paguei. E agora?", "Como falo com meu banco
com segurança?"), e cada resposta tem o botão **Ouvir resposta** (voz do próprio navegador). No fim
de uma análise de mensagem, o botão **Tirar dúvidas sobre esta análise** abre o chat já com o
resumo daquela análise.

- **Nada é guardado:** o histórico fica só na página e é enviado a cada pergunta; some ao fechar.
- **Privacidade:** CPF, telefone, e-mail e cartão são ocultados antes de ir para a IA.
- **Segurança:** o agente (`agente/prompt_conversa.md`) reaproveita as seções 3 e 4 do
  `prompt_sistema.md`. O backend apaga links e telefones que a IA escrever (menos sites `.gov.br`),
  não deixa o risco cair abaixo do que as regras acharam em casos graves e mostra os contatos de
  ajuda (CVV 188, 190, Disque 100, SaferNet) com texto fixo.
- **Limites:** até 6 perguntas por conversa e `LIMITE_POR_MINUTO` pedidos por minuto.
- **Sem IA:** as regras automáticas respondem às situações mais comuns (golpe detectado, "já caí",
  falar com o banco, verificação em duas etapas, link seguro, "explica mais simples").

### Moderação de casos reais (CRUD)

O detector aprende com casos reais cadastrados **pela equipe** em **http://127.0.0.1:8000/admin.html**
(a página não aparece no menu do site). Cada caso tem texto, plataforma, rótulo (golpe ou não),
táticas, golpe parecido da base, lição e status (`pendente`, `aprovado`, `rejeitado`).

- O botão **Sugerir táticas** usa as regras automáticas (sem IA, sem gastar cota) para pré-preencher
  táticas, golpe parecido e rótulo. Revise antes de salvar.
- O texto é **anonimizado ao salvar** (CPF, telefone, e-mail, cartão viram `[CPF]`, `[TELEFONE]`…).
- Só casos **aprovados** entram no prompt da IA, até 5 por análise, escolhidos por semelhança
  (`backend/app/similares.py`). Marque cerca de 1 em cada 5 aprovados como **reservado para teste**:
  eles não vão para a IA e servem para medir se o detector acerta.
- Os casos ficam em `backend/alo_seguro.db` (SQLite), criado na primeira vez e **fora do Git**:
  cada computador tem o seu banco.
- **Sem senha, por decisão da equipe:** as rotas `/api/v1/admin/...` só aceitam pedidos feitos no
  próprio computador que roda o servidor (127.0.0.1). Atenção: se um dia o site for publicado atrás
  de um proxy (Nginx, Render, Railway…), todos os pedidos podem parecer vir de 127.0.0.1; antes disso,
  é preciso adicionar uma senha ou login.

### Problemas com a chave do Gemini

Se a análise mostrar "O Google não liberou o plano gratuito da IA para o projeto desta chave", o
Google bloqueou o nível gratuito para aquele projeto (erro `403 PERMISSION_DENIED`). Criar outra
chave **no mesmo projeto** não resolve. Tente, nesta ordem:

1. Abra [aistudio.google.com/projects](https://aistudio.google.com/projects) e veja o status do projeto.
   Se aparecer **"Verification needed"**, clique em **Verify project** e confirme pelo celular (QR code).
2. Confira se a data de nascimento da conta Google indica **18 anos ou mais**
   ([myaccount.google.com/birthday](https://myaccount.google.com/birthday)). Contas institucionais
   (Workspace for Education) dependem do administrador.
3. Crie um **projeto novo** no AI Studio, gere a chave nele e troque no `backend/.env`.
4. Use a chave de outra pessoa do grupo cujo projeto tenha o plano gratuito liberado.

Enquanto isso, o site continua funcionando com as regras automáticas.

Para manter este README confiável:

- não inclua comandos ou variáveis que não existam no projeto;

- publique um `.env.example` sem credenciais reais;

- descreva separadamente como executar em desenvolvimento e em produção;

- documente os testes e os requisitos de versão do Python e de outras ferramentas.

## Roadmap

O roadmap abaixo é uma sugestão de organização, não uma promessa de entrega.

- [ ] Definir escopo do MVP, campos obrigatórios e critérios de consulta.

- [ ] Mapear fontes de dados permitidas, confiáveis e tecnicamente acessíveis.

- [ ] Criar protótipo da interface e validar a linguagem com usuários.

- [ ] Implementar formulário acessível e estados de carregamento, erro e resultado.

- [ ] Definir contrato da API e separar regras de negócio das integrações.

- [ ] Implementar validações e testes automatizados.

- [ ] Revisar privacidade, retenção, logs e medidas contra abuso.

- [ ] Documentar instalação, execução e limitações reais do produto.

- [ ] Avaliar implantação e estratégia de escala com base em métricas e requisitos.

## Status do projeto

**Em desenvolvimento.** Este repositório faz parte de um projeto acadêmico. As funcionalidades, integrações e garantias de privacidade devem ser consideradas planejadas até que estejam implementadas, testadas e documentadas.

## Equipe

| Integrante |
| --- |
| Ben Rocha |
| Roberto Lucas |
| Diego Gabriel |
| Irardes Santos |
| Miguel Martus |

## Contribuição

Sugestões e contribuições são bem-vindas. Antes de abrir uma contribuição, verifique o escopo acadêmico do projeto e não envie dados pessoais reais, credenciais ou exemplos contendo informações sensíveis. Issues e pull requests devem descrever o problema, a mudança proposta e como ela foi validada.

## Licença

A licença ainda não foi informada. Antes de permitir reutilização ou redistribuição do código, defina uma licença apropriada e adicione o respectivo arquivo ao repositório.

---

**Repositório:** [github.com/IrardesLuna/alo_seguro](https://github.com/IrardesLuna/alo_seguro)
