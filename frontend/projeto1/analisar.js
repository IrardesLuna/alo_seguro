(function () {
  // -----------------------------------------------------------------------
  // Aba "Analisar mensagem": envia o texto para a API (backend/app/main.py),
  // que usa a IA (Gemini) + regras automáticas, e mostra o resultado.
  // A chave da IA fica só no servidor, nunca aqui no navegador.
  // -----------------------------------------------------------------------
  'use strict';

  // Se o site for aberto pelo próprio servidor (porta 8000), a API está no mesmo endereço.
  // Se for aberto direto do arquivo ou pelo Live Server, usamos o servidor local.
  // (o endereço é calculado em proj1.js, que carrega antes deste arquivo)
  var API_BASE = window.ALO_SEGURO_API_BASE !== undefined ? window.ALO_SEGURO_API_BASE
    : (location.protocol === 'file:' || location.port === '5500' || location.port === '5501') ? 'http://127.0.0.1:8000' : '';

  var NIVEIS = {
    baixo: { rotulo: 'Risco baixo', icone: 'ti-shield-check' },
    medio: { rotulo: 'Risco médio', icone: 'ti-alert-circle' },
    alto: { rotulo: 'Risco alto', icone: 'ti-alert-triangle' },
    muito_alto: { rotulo: 'Risco muito alto', icone: 'ti-alert-octagon' }
  };

  var TIPOS_LINK = {
    legitimo_provavel: 'Provavelmente legítimo',
    loja_falsa: 'Possível loja falsa',
    roubo_de_dados: 'Possível roubo de dados',
    download_malicioso: 'Download perigoso',
    fraude_financeira: 'Possível fraude financeira',
    indeterminado: 'Sem conclusão'
  };

  var PASSOS_SE_JA_CAIU = [
    'Se pagou por Pix: fale agora com o seu banco pelo app ou telefone oficial e peça o MED (Mecanismo Especial de Devolução).',
    'Registre um boletim de ocorrência (pode ser pela delegacia online do seu estado).',
    'Guarde prints da conversa, números, links e comprovantes: são provas.',
    'Se passou código ou senha: recupere a conta pelo app oficial, troque as senhas e ative a verificação em duas etapas.',
    'Avise seus contatos, porque o golpista pode tentar enganá-los usando o seu nome.'
  ];

  function lerStorage(chave) { try { return sessionStorage.getItem(chave); } catch (e) { return null; } }
  function gravarStorage(chave, valor) { try { sessionStorage.setItem(chave, valor); } catch (e) { /* segue sem salvar */ } }

  // Cria elementos com segurança: o texto vindo da IA nunca vira HTML (evita XSS).
  function el(tag, atributos, filhos) {
    var elemento = document.createElement(tag);
    Object.keys(atributos || {}).forEach(function (nome) {
      if (nome === 'texto') elemento.textContent = atributos[nome];
      else elemento.setAttribute(nome, atributos[nome]);
    });
    (filhos || []).forEach(function (filho) {
      if (filho) elemento.appendChild(typeof filho === 'string' ? document.createTextNode(filho) : filho);
    });
    return elemento;
  }

  function icone(nome) { return el('i', { 'class': 'ti ' + nome, 'aria-hidden': 'true' }); }

  // ---------------------------------------------------------------------
  // Abas
  // ---------------------------------------------------------------------
  var abas = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));

  function abrirAba(aba, darFoco) {
    abas.forEach(function (outra) {
      var selecionada = outra === aba;
      outra.setAttribute('aria-selected', String(selecionada));
      outra.tabIndex = selecionada ? 0 : -1;
      document.getElementById(outra.getAttribute('aria-controls')).hidden = !selecionada;
    });
    if (darFoco) aba.focus();
    gravarStorage('alo-seguro-aba', aba.id);
  }

  abas.forEach(function (aba, indice) {
    aba.addEventListener('click', function () { abrirAba(aba, false); });
    aba.addEventListener('keydown', function (evento) {
      var destino = null;
      if (evento.key === 'ArrowRight') destino = abas[(indice + 1) % abas.length];
      else if (evento.key === 'ArrowLeft') destino = abas[(indice - 1 + abas.length) % abas.length];
      else if (evento.key === 'Home') destino = abas[0];
      else if (evento.key === 'End') destino = abas[abas.length - 1];
      if (destino) { evento.preventDefault(); abrirAba(destino, true); }
    });
  });

  var ABAS_POR_ENDERECO = { '#analisar': 'aba-mensagem', '#conversar': 'aba-conversa' };
  var abaInicial = ABAS_POR_ENDERECO[location.hash] || lerStorage('alo-seguro-aba');
  if (abaInicial && document.getElementById(abaInicial)) abrirAba(document.getElementById(abaInicial), false);

  // ---------------------------------------------------------------------
  // Formulário
  // ---------------------------------------------------------------------
  var form = document.getElementById('analise-form');
  var campo = document.getElementById('f-mensagem');
  var rotulo = document.getElementById('rotulo-mensagem');
  var dica = document.getElementById('dica-mensagem');
  var contador = document.getElementById('contador-mensagem');
  var erro = document.getElementById('err-mensagem');
  var botao = document.getElementById('analise-btn');
  var carregando = document.getElementById('analise-carregando');
  var resultado = document.getElementById('analise-resultado');
  var novaAnalise = document.getElementById('analise-nova');

  function canalEscolhido() {
    var marcado = form.querySelector('input[name="canal"]:checked');
    return marcado ? marcado.value : 'redes_sociais';
  }

  // Texto do campo para cada opção de "O que você quer analisar?"
  var TEXTOS_DO_CAMPO = {
    redes_sociais: {
      rotulo: 'Cole a mensagem recebida',
      exemplo: 'Ex.: Oi mãe, esse é meu número novo. Consegue me fazer um Pix urgente?',
      dica: 'Copie o texto completo, com links e o nome de quem enviou. Se quiser, diga onde recebeu (ex.: "recebi no Facebook").'
    },
    email: {
      rotulo: 'Cole o e-mail recebido',
      exemplo: 'Ex.: De: Banco <alerta@banco-seguranca.com> — Sua conta será bloqueada...',
      dica: 'Inclua o remetente (De:), o assunto e o texto completo, com os links.'
    },
    links: {
      rotulo: 'Cole o link recebido',
      exemplo: 'Ex.: https://nubank-seguranca-app.com/login',
      dica: 'Pode colar um ou mais links. Nós não abrimos o link: analisamos só o endereço.'
    }
  };

  function atualizarCampoPorCanal() {
    var textos = TEXTOS_DO_CAMPO[canalEscolhido()] || TEXTOS_DO_CAMPO.redes_sociais;
    rotulo.textContent = textos.rotulo;
    campo.placeholder = textos.exemplo;
    dica.textContent = textos.dica;
  }

  var NOMES_DAS_REDES = {
    whatsapp: 'WhatsApp', instagram: 'Instagram', facebook: 'Facebook', linkedin: 'LinkedIn',
    telegram: 'Telegram', tiktok: 'TikTok', snapchat: 'Snapchat', discord: 'Discord', sms: 'SMS', x: 'X (Twitter)'
  };

  function mostrarErro(mensagem) {
    erro.textContent = mensagem;
    erro.classList.add('show');
    campo.classList.add('invalid');
    campo.setAttribute('aria-invalid', 'true');
  }

  function limparErro() {
    erro.classList.remove('show');
    campo.classList.remove('invalid');
    campo.setAttribute('aria-invalid', 'false');
  }

  form.querySelectorAll('input[name="canal"]').forEach(function (opcao) {
    opcao.addEventListener('change', atualizarCampoPorCanal);
  });

  campo.addEventListener('input', function () {
    contador.textContent = campo.value.length + ' / 6000';
    limparErro();
  });

  // ---------------------------------------------------------------------
  // Montagem do resultado
  // ---------------------------------------------------------------------
  function secao(titulo, nomeIcone) {
    return el('h3', { 'class': 'secao-titulo' }, [icone(nomeIcone), titulo]);
  }

  function montarMedidor(dados) {
    var nivel = NIVEIS[dados.nivel] ? dados.nivel : 'medio';
    var preenchida = el('div', { 'class': 'barra-preenchida' });
    var titulo = el('h2', { texto: dados.veredito, tabindex: '-1' });
    var medidor = el('div', { 'class': 'medidor nivel-' + nivel }, [
      el('div', { 'class': 'medidor-topo' }, [
        el('div', { 'class': 'medidor-numero' }, [dados.probabilidade_golpe + '%', el('small', { texto: 'de chance de ser golpe' })]),
        el('span', { 'class': 'selo-nivel' }, [icone(NIVEIS[nivel].icone), NIVEIS[nivel].rotulo])
      ]),
      el('div', { 'class': 'barra', role: 'img', 'aria-label': dados.probabilidade_golpe + '% de chance de ser golpe' }, [preenchida]),
      el('div', { 'class': 'barra-escala', 'aria-hidden': 'true' }, [el('span', { texto: '1%' }), el('span', { texto: '99%' })]),
      titulo,
      el('p', { texto: dados.explicacao })
    ]);
    // anima a barra depois que ela aparece na tela
    setTimeout(function () { preenchida.style.width = dados.probabilidade_golpe + '%'; }, 30);
    return medidor;
  }

  function montarRedFlags(dados) {
    var pesoPorTatica = {};
    (dados.taticas_info || []).forEach(function (t) { pesoPorTatica[t.id] = t; });

    var bloco = el('div', {}, [secao('Sinais de alerta (red flags)', 'ti-flag-3')]);
    dados.red_flags.forEach(function (flag) {
      var info = pesoPorTatica[flag.tatica];
      var cartao = el('div', { 'class': 'flag' }, [
        info ? el('span', { 'class': 'etiqueta ' + info.peso, texto: info.nome }) : null,
        flag.trecho ? el('div', { 'class': 'flag-trecho', texto: '“' + flag.trecho + '”' }) : null,
        el('p', { texto: flag.explicacao })
      ]);
      bloco.appendChild(cartao);
    });
    return bloco;
  }

  function montarLinks(dados) {
    var bloco = el('div', {}, [secao(dados.analise_link.length > 1 ? 'Análise dos links' : 'Análise do link', 'ti-link')]);
    dados.analise_link.forEach(function (link) {
      var classeTipo = link.tipo === 'legitimo_provavel' ? 'ok' : (link.tipo === 'indeterminado' ? '' : 'perigo');
      var lista = el('ul');
      (link.motivos || []).forEach(function (motivo) { lista.appendChild(el('li', { texto: motivo })); });
      bloco.appendChild(el('div', { 'class': 'link-card' }, [
        el('div', { 'class': 'link-url', texto: link.url }),
        el('div', { 'class': 'link-meta' }, [
          el('span', { 'class': 'etiqueta tipo-link ' + classeTipo, texto: TIPOS_LINK[link.tipo] || 'Sem conclusão' }),
          link.dominio_real ? el('span', {}, ['Domínio real: ', el('code', { texto: link.dominio_real })]) : null
        ]),
        link.motivos && link.motivos.length ? lista : el('p', { 'class': 'observacao', texto: 'Nenhum sinal técnico de fraude no endereço.' })
      ]));
    });
    return bloco;
  }

  function montarLista(titulo, nomeIcone, itens, numerada) {
    var lista = el(numerada ? 'ol' : 'ul', { 'class': numerada ? 'steps-list' : 'tips-list' });
    itens.forEach(function (texto, i) {
      lista.appendChild(numerada
        ? el('li', {}, [el('span', { 'class': 'n', texto: String(i + 1) }), el('span', { texto: texto })])
        : el('li', {}, [icone('ti-circle-check'), el('span', { texto: texto })]));
    });
    return el('div', {}, [secao(titulo, nomeIcone), lista]);
  }

  function renderizar(dados) {
    resultado.innerHTML = '';
    var partes = [];

    if (dados.aviso_ajuda) {
      partes.push(el('div', { 'class': 'aviso aviso-ajuda', role: 'note' }, [
        icone('ti-lifebuoy'), el('div', {}, [el('strong', { texto: 'Você não está sozinho. Procure ajuda: ' }), dados.aviso_ajuda])
      ]));
    }
    if (dados.aviso_sistema) {
      partes.push(el('div', { 'class': 'aviso aviso-sistema', role: 'note' }, [icone('ti-info-circle'), el('span', { texto: dados.aviso_sistema })]));
    }

    partes.push(montarMedidor(dados));

    // Em "rede social", mostra qual rede a IA identificou pelo texto.
    var rede = NOMES_DAS_REDES[(dados.canal_analisado || '').toLowerCase()];
    if (rede && canalEscolhido() === 'redes_sociais') {
      partes.push(el('p', { 'class': 'canal-identificado' }, ['Rede provável: ', el('strong', { texto: rede })]));
    }

    if (dados.golpe_parecido) {
      partes.push(el('p', { 'class': 'parecido' }, [
        'Parecido com: ', el('strong', { texto: dados.golpe_parecido.nome }),
        ' (' + dados.golpe_parecido.similaridade + '% de semelhança com golpes conhecidos)'
      ]));
    }

    if (dados.red_flags && dados.red_flags.length) partes.push(montarRedFlags(dados));

    if (dados.taticas_info && dados.taticas_info.length) {
      var etiquetas = el('div', { 'class': 'etiquetas' });
      dados.taticas_info.forEach(function (t) {
        etiquetas.appendChild(el('span', { 'class': 'etiqueta ' + t.peso, texto: t.nome }));
      });
      partes.push(el('div', {}, [secao('Táticas de manipulação encontradas', 'ti-tags'), etiquetas]));
    }

    if (dados.dicas && dados.dicas.length) {
      var tituloDicas = (dados.nivel === 'baixo' || dados.nivel === 'medio')
        ? 'Como ter certeza de que não é golpe'
        : 'Como confirmar antes de agir';
      partes.push(montarLista(tituloDicas, 'ti-checklist', dados.dicas, true));
    }
    if (dados.analise_link && dados.analise_link.length) partes.push(montarLinks(dados));
    if (dados.sinais_de_legitimidade && dados.sinais_de_legitimidade.length) {
      partes.push(montarLista('Pontos a favor', 'ti-thumb-up', dados.sinais_de_legitimidade, false));
    }

    var passos = (dados.se_ja_caiu && dados.se_ja_caiu.length) ? dados.se_ja_caiu
      : (dados.nivel === 'alto' || dados.nivel === 'muito_alto') ? PASSOS_SE_JA_CAIU : [];
    if (passos.length) {
      var listaPassos = el('ol', { 'class': 'steps-list' });
      passos.forEach(function (texto, i) {
        listaPassos.appendChild(el('li', {}, [el('span', { 'class': 'n', texto: String(i + 1) }), el('span', { texto: texto })]));
      });
      var detalhes = el('details', { 'class': 'ja-caiu' }, [el('summary', { texto: 'Já pagou, clicou ou enviou algo? Veja o que fazer agora' }), listaPassos]);
      if (dados.se_ja_caiu && dados.se_ja_caiu.length) detalhes.open = true;
      partes.push(detalhes);
    }

    if (dados.observacoes) partes.push(el('p', { 'class': 'observacao', texto: dados.observacoes }));

    var origem = dados.origem === 'ia'
      ? 'Análise feita por IA (Google Gemini) com apoio de regras automáticas.'
      : 'Análise feita só com as regras automáticas do Alô Seguro.';
    if (dados.dados_ocultados > 0) {
      origem += ' Ocultamos ' + dados.dados_ocultados + (dados.dados_ocultados === 1 ? ' dado pessoal' : ' dados pessoais') + ' antes de analisar.';
    }
    partes.push(el('p', { 'class': 'rodape-analise', texto: origem + ' Isto é uma estimativa: na dúvida, confirme sempre por outro canal.' }));

    // Leva o resumo desta análise para a aba "Tirar dúvidas" (conversa.js).
    if (window.AloSeguroConversa) {
      var duvidas = el('button', { type: 'button', 'class': 'btn btn-duvidas' }, [icone('ti-messages'), el('span', { texto: 'Tirar dúvidas sobre esta análise' })]);
      duvidas.addEventListener('click', function () {
        window.AloSeguroConversa.abrirComAnalise({
          probabilidade_golpe: dados.probabilidade_golpe,
          nivel: dados.nivel,
          veredito: dados.veredito,
          golpe_parecido: dados.golpe_parecido ? dados.golpe_parecido.nome : '',
          taticas: dados.taticas_detectadas || []
        });
      });
      partes.push(duvidas);
    }

    partes.forEach(function (parte) { resultado.appendChild(parte); });
    resultado.classList.add('show');
    var titulo = resultado.querySelector('h2');
    if (titulo) titulo.focus();
  }

  // ---------------------------------------------------------------------
  // Envio
  // ---------------------------------------------------------------------
  function definirCarregando(ativo) {
    botao.disabled = ativo;
    botao.querySelector('span').textContent = ativo ? 'Analisando…' : 'Analisar mensagem';
    carregando.classList.toggle('show', ativo);
  }

  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    var texto = campo.value.trim();
    if (texto.length < 3) {
      mostrarErro('Cole a mensagem ou o link que você recebeu.');
      campo.focus();
      return;
    }

    limparErro();
    resultado.classList.remove('show');
    resultado.innerHTML = '';
    novaAnalise.style.display = 'none';
    definirCarregando(true);

    fetch(API_BASE + '/api/analisar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plataforma: canalEscolhido(), texto: texto })
    })
      .then(function (resposta) {
        return resposta.json().catch(function () { return {}; }).then(function (corpo) {
          if (!resposta.ok) {
            var detalhe = typeof corpo.detail === 'string' ? corpo.detail : 'Não foi possível analisar agora. Tente de novo.';
            throw new Error(detalhe);
          }
          return corpo;
        });
      })
      .then(function (dados) {
        renderizar(dados);
        novaAnalise.style.display = 'inline-flex';
      })
      .catch(function (falha) {
        var mensagem = falha instanceof TypeError
          ? 'Não conseguimos falar com o servidor do Alô Seguro. Ele está ligado? (veja "Como rodar" no README)'
          : falha.message;
        mostrarErro(mensagem);
        campo.focus();
      })
      .then(function () { definirCarregando(false); });
  });

  novaAnalise.addEventListener('click', function () {
    form.reset();
    atualizarCampoPorCanal();
    contador.textContent = '0 / 6000';
    resultado.classList.remove('show');
    resultado.innerHTML = '';
    novaAnalise.style.display = 'none';
    limparErro();
    campo.focus();
  });

  atualizarCampoPorCanal();
})();
