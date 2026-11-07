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

### Exemplo de fluxo da API (proposto)

Os caminhos abaixo são apenas uma proposta para orientar o desenho; **não representam endpoints confirmados ou já implementados**.

| Método | Caminho proposto | Finalidade |
| --- | --- | --- |
| `GET` | `/health` | Verificar disponibilidade básica do serviço |
| `POST` | `/api/v1/check` | Solicitar uma consulta validada |

A resposta de consulta deve usar um formato previsível e evitar incluir dados que não sejam necessários para explicar o resultado. Autenticação, limites, consentimento, retenção e requisitos das fontes precisam ser definidos antes de uma publicação real.

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
│   ├── tests/
│   └── requirements.txt
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## Começando

O procedimento exato depende dos arquivos e dependências presentes no repositório. Quando a configuração do projeto estiver definida, documente aqui os comandos testados para instalar dependências, configurar variáveis e iniciar front-end e API.

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
