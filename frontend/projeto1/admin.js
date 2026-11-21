(function () {
  // -----------------------------------------------------------------------
  // Página de moderação dos casos reais (CRUD em /api/v1/admin/casos).
  // Só funciona no computador que roda o servidor: a API recusa pedidos de fora.
  // -----------------------------------------------------------------------
  'use strict';

  var API = (location.protocol === 'file:' || location.port === '5500' || location.port === '5501') ? 'http://127.0.0.1:8000' : '';
  var URL_CASOS = API + '/api/v1/admin/casos';

  // Tema e tamanho de fonte escolhidos no site principal
  try {
    document.documentElement.setAttribute('data-theme', localStorage.getItem('alo-seguro-theme') === 'light' ? 'light' : 'dark');
    var fonte = Number(localStorage.getItem('alo-seguro-font-size'));
    if (fonte >= 1 && fonte <= 5) document.body.setAttribute('data-font-size', String(fonte));
  } catch (e) { document.documentElement.setAttribute('data-theme', 'dark'); }

  var NOMES_STATUS = { pendente: 'Pendente', aprovado: 'Aprovado', rejeitado: 'Rejeitado' };
  var opcoes = null;
  var nomesPlataforma = {};
  var nomesTatica = {};
  var nomesGolpe = {};

  var $ = function (id) { return document.getElementById(id); };
  var form = $('caso-form');
  var campos = {
    id: $('caso-id'), plataforma: $('caso-plataforma'), texto: $('caso-texto'), golpe: $('caso-golpe'),
    status: $('caso-status'), licao: $('caso-licao'), reservado: $('caso-reservado')
  };

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

  function api(metodo, url, corpo) {
    return fetch(url, {
      method: metodo,
      headers: corpo ? { 'Content-Type': 'application/json' } : {},
      body: corpo ? JSON.stringify(corpo) : undefined
    }).then(function (resposta) {
      if (resposta.status === 204) return null;
      return resposta.json().catch(function () { return {}; }).then(function (dados) {
        if (!resposta.ok) {
          var detalhe = typeof dados.detail === 'string' ? dados.detail
            : Array.isArray(dados.detail) ? 'Confira os campos do formulário.' : 'Algo deu errado. Tente de novo.';
          throw new Error(detalhe);
        }
        return dados;
      });
    }, function () {
      throw new Error('Não conseguimos falar com o servidor. Ele está ligado? (veja "Como rodar" no README)');
    });
  }

  function erroGeral(mensagem) {
    $('admin-erro-geral').hidden = !mensagem;
    $('admin-erro-geral-texto').textContent = mensagem || '';
  }

  function avisar(mensagemErro, mensagemOk) {
    $('caso-erro').textContent = mensagemErro || '';
    $('caso-erro').classList.toggle('show', !!mensagemErro);
    $('caso-ok').textContent = mensagemOk || '';
  }

  // ---------------------------------------------------------------------
  // Opções do formulário
  // ---------------------------------------------------------------------
  function montarOpcoes(dados) {
    opcoes = dados;
    dados.plataformas.forEach(function (p) {
      nomesPlataforma[p.id] = p.nome;
      campos.plataforma.appendChild(el('option', { value: p.id, texto: p.nome }));
      $('filtro-plataforma').appendChild(el('option', { value: p.id, texto: p.nome }));
    });
    var caixa = $('caso-taticas');
    dados.taticas.forEach(function (t) {
      nomesTatica[t.id] = t.nome;
      caixa.appendChild(el('label', { 'class': 'tatica-opcao peso-' + t.peso }, [
        el('input', { type: 'checkbox', name: 'tatica', value: t.id }),
        el('span', { texto: t.nome })
      ]));
    });
    var lista = $('lista-golpes');
    dados.golpes.forEach(function (g) {
      nomesGolpe[g.id] = g.nome;
      lista.appendChild(el('option', { value: g.id, texto: g.nome }));
    });
  }

  function mostrarNomeGolpe() {
    var id = campos.golpe.value.trim();
    $('nome-golpe').textContent = !id ? '' : nomesGolpe[id] ? nomesGolpe[id] : 'Este id não existe na base.';
  }
  campos.golpe.addEventListener('input', mostrarNomeGolpe);

  function taticasMarcadas() {
    return Array.prototype.map.call(form.querySelectorAll('input[name="tatica"]:checked'), function (c) { return c.value; });
  }
  function marcarTaticas(lista) {
    Array.prototype.forEach.call(form.querySelectorAll('input[name="tatica"]'), function (c) { c.checked = lista.indexOf(c.value) > -1; });
  }

  // ---------------------------------------------------------------------
  // Formulário: criar, editar, sugerir
  // ---------------------------------------------------------------------
  function limparFormulario() {
    form.reset();
    campos.id.value = '';
    marcarTaticas([]);
    mostrarNomeGolpe();
    $('titulo-form').textContent = 'Novo caso';
    $('btn-salvar').querySelector('span').textContent = 'Salvar caso';
    $('btn-cancelar').hidden = true;
  }

  function editar(caso) {
    campos.id.value = caso.id;
    campos.plataforma.value = caso.plataforma;
    campos.texto.value = caso.texto;
    form.querySelector('input[name="rotulo"][value="' + caso.rotulo + '"]').checked = true;
    marcarTaticas(caso.taticas);
    campos.golpe.value = caso.golpe_base || '';
    campos.status.value = caso.status;
    campos.licao.value = caso.licao || '';
    campos.reservado.checked = caso.reservado_para_teste;
    mostrarNomeGolpe();
    avisar('', '');
    $('titulo-form').textContent = 'Editando caso #' + caso.id;
    $('btn-salvar').querySelector('span').textContent = 'Salvar alterações';
    $('btn-cancelar').hidden = false;
    $('titulo-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
    campos.texto.focus();
  }

  $('btn-cancelar').addEventListener('click', function () { limparFormulario(); avisar('', ''); });

  $('btn-sugerir').addEventListener('click', function () {
    var botao = this;
    botao.disabled = true;
    avisar('', '');
    api('POST', URL_CASOS + '/sugestao', { plataforma: campos.plataforma.value, texto: campos.texto.value })
      .then(function (s) {
        campos.texto.value = s.texto;
        marcarTaticas(s.taticas);
        if (s.golpe_base && !campos.golpe.value) campos.golpe.value = s.golpe_base;
        form.querySelector('input[name="rotulo"][value="' + s.rotulo_sugerido + '"]').checked = true;
        mostrarNomeGolpe();
        avisar('', 'Sugestão das regras automáticas (' + s.probabilidade_golpe + '% de chance de golpe). Revise antes de salvar.' +
          (s.dados_ocultados ? ' Ocultamos ' + s.dados_ocultados + ' dado(s) pessoal(is).' : ''));
      })
      .catch(function (falha) { avisar(falha.message); })
      .then(function () { botao.disabled = false; });
  });

  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    var id = campos.id.value;
    var corpo = {
      plataforma: campos.plataforma.value,
      texto: campos.texto.value,
      rotulo: form.querySelector('input[name="rotulo"]:checked').value,
      taticas: taticasMarcadas(),
      golpe_base: campos.golpe.value.trim() || null,
      licao: campos.licao.value,
      status: campos.status.value,
      reservado_para_teste: campos.reservado.checked
    };
    $('btn-salvar').disabled = true;
    api(id ? 'PATCH' : 'POST', id ? URL_CASOS + '/' + id : URL_CASOS, corpo)
      .then(function (dados) {
        var msg = (id ? 'Caso #' + id + ' atualizado.' : 'Caso #' + dados.caso.id + ' criado.') +
          (dados.dados_ocultados ? ' Ocultamos ' + dados.dados_ocultados + ' dado(s) pessoal(is) do texto.' : '');
        limparFormulario();
        avisar('', msg);
        carregarLista();
      })
      .catch(function (falha) { avisar(falha.message); })
      .then(function () { $('btn-salvar').disabled = false; });
  });

  // ---------------------------------------------------------------------
  // Lista
  // ---------------------------------------------------------------------
  function mudarStatus(caso, status) {
    api('PATCH', URL_CASOS + '/' + caso.id, { status: status })
      .then(carregarLista)
      .catch(function (falha) { erroGeral(falha.message); });
  }

  // Exclusão em dois cliques, sem caixa de diálogo do navegador.
  function botaoExcluir(caso) {
    var b = el('button', { type: 'button', 'class': 'btn-acao perigo' }, [icone('ti-trash'), el('span', { texto: 'Excluir' })]);
    var confirmando = false;
    var tempo = null;
    b.addEventListener('click', function () {
      if (!confirmando) {
        confirmando = true;
        b.querySelector('span').textContent = 'Confirmar exclusão';
        b.classList.add('confirmando');
        tempo = setTimeout(function () { confirmando = false; b.querySelector('span').textContent = 'Excluir'; b.classList.remove('confirmando'); }, 4000);
        return;
      }
      clearTimeout(tempo);
      api('DELETE', URL_CASOS + '/' + caso.id)
        .then(function () { if (campos.id.value === String(caso.id)) limparFormulario(); carregarLista(); })
        .catch(function (falha) { erroGeral(falha.message); });
    });
    return b;
  }

  function itemDaLista(caso) {
    var acoes = [el('button', { type: 'button', 'class': 'btn-acao' }, [icone('ti-pencil'), el('span', { texto: 'Editar' })])];
    acoes[0].addEventListener('click', function () { editar(caso); });
    if (caso.status !== 'aprovado') {
      var aprovar = el('button', { type: 'button', 'class': 'btn-acao ok' }, [icone('ti-check'), el('span', { texto: 'Aprovar' })]);
      aprovar.addEventListener('click', function () { mudarStatus(caso, 'aprovado'); });
      acoes.push(aprovar);
    }
    if (caso.status !== 'rejeitado') {
      var rejeitar = el('button', { type: 'button', 'class': 'btn-acao' }, [icone('ti-x'), el('span', { texto: 'Rejeitar' })]);
      rejeitar.addEventListener('click', function () { mudarStatus(caso, 'rejeitado'); });
      acoes.push(rejeitar);
    }
    acoes.push(botaoExcluir(caso));

    var etiquetas = [
      el('span', { 'class': 'etiqueta status-' + caso.status, texto: NOMES_STATUS[caso.status] }),
      el('span', { 'class': 'etiqueta', texto: nomesPlataforma[caso.plataforma] || caso.plataforma }),
      el('span', { 'class': 'etiqueta ' + (caso.rotulo === 'golpe' ? 'forte' : ''), texto: caso.rotulo === 'golpe' ? 'Golpe' : 'Não é golpe' })
    ];
    if (caso.reservado_para_teste) etiquetas.push(el('span', { 'class': 'etiqueta', texto: 'Reservado para teste' }));
    if (caso.golpe_base) etiquetas.push(el('span', { 'class': 'etiqueta', texto: caso.golpe_base + ' · ' + (nomesGolpe[caso.golpe_base] || '') }));

    return el('li', { 'class': 'admin-caso' }, [
      el('div', { 'class': 'admin-caso-topo' }, [el('strong', { texto: '#' + caso.id }), el('div', { 'class': 'etiquetas' }, etiquetas)]),
      el('p', { 'class': 'admin-caso-texto', texto: caso.texto }),
      caso.taticas.length ? el('p', { 'class': 'admin-caso-meta', texto: 'Táticas: ' + caso.taticas.map(function (t) { return nomesTatica[t] || t; }).join(', ') }) : null,
      caso.licao ? el('p', { 'class': 'admin-caso-meta', texto: 'Lição: ' + caso.licao }) : null,
      el('div', { 'class': 'admin-caso-acoes' }, acoes)
    ]);
  }

  var atraso = null;
  function carregarLista() {
    var params = new URLSearchParams();
    if ($('filtro-status').value) params.set('status', $('filtro-status').value);
    if ($('filtro-plataforma').value) params.set('plataforma', $('filtro-plataforma').value);
    if ($('filtro-busca').value.trim()) params.set('busca', $('filtro-busca').value.trim());
    params.set('limite', '200');
    return api('GET', URL_CASOS + '?' + params.toString())
      .then(function (dados) {
        erroGeral('');
        var c = dados.contagem;
        $('admin-contagem').textContent = 'Mostrando ' + dados.casos.length + ' de ' + dados.total + ' · No banco: ' +
          c.pendente + ' pendente(s), ' + c.aprovado + ' aprovado(s), ' + c.rejeitado + ' rejeitado(s).';
        var lista = $('admin-casos');
        lista.textContent = '';
        if (!dados.casos.length) lista.appendChild(el('li', { 'class': 'admin-vazio', texto: 'Nenhum caso encontrado.' }));
        dados.casos.forEach(function (caso) { lista.appendChild(itemDaLista(caso)); });
      })
      .catch(function (falha) { erroGeral(falha.message); });
  }

  ['filtro-status', 'filtro-plataforma'].forEach(function (id) { $(id).addEventListener('change', carregarLista); });
  $('filtro-busca').addEventListener('input', function () { clearTimeout(atraso); atraso = setTimeout(carregarLista, 300); });

  api('GET', API + '/api/v1/admin/opcoes')
    .then(function (dados) { montarOpcoes(dados); return carregarLista(); })
    .catch(function (falha) { erroGeral(falha.message); });
})();
