(function () {
  // ---------------------------------------------------------------------
  // Aba "Verificar vazamento": envia e-mail e/ou telefone para a API
  // (POST /api/v1/check em backend/app/main.py). O servidor consulta as
  // fontes configuradas (base de demonstração ou Have I Been Pwned) e
  // devolve o resultado com recomendações. Nenhuma chave fica no navegador.
  // ---------------------------------------------------------------------
  'use strict';

  // Se o site for aberto pelo próprio servidor (porta 8000), a API está no mesmo endereço.
  // Se for aberto direto do arquivo ou pelo Live Server, usamos o servidor local.
  var API_BASE = window.ALO_SEGURO_API !== undefined ? window.ALO_SEGURO_API
    : (location.protocol === 'file:' || location.port === '5500' || location.port === '5501') ? 'http://127.0.0.1:8000' : '';
  window.ALO_SEGURO_API_BASE = API_BASE; // usado também por analisar.js

  function lerStorage(chave) { try { return localStorage.getItem(chave); } catch (e) { return null; } }
  function gravarStorage(chave, valor) { try { localStorage.setItem(chave, valor); } catch (e) { /* storage bloqueado: segue sem salvar */ } }

  var themeToggle = document.getElementById('theme-toggle');
  var decreaseFont = document.getElementById('font-decrease');
  var increaseFont = document.getElementById('font-increase');
  var fontLevel = document.getElementById('font-level');
  var savedTheme = lerStorage('alo-seguro-theme');
  var savedFontSize = Number(lerStorage('alo-seguro-font-size')) || 3;
  var fontSize = Math.min(5, Math.max(1, savedFontSize));

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    var dark = theme === 'dark';
    themeToggle.querySelector('span').textContent = dark ? 'Modo claro' : 'Modo escuro';
    themeToggle.querySelector('i').className = dark ? 'ti ti-sun' : 'ti ti-moon';
    gravarStorage('alo-seguro-theme', theme);
  }

  function applyFontSize(level) {
    fontSize = Math.min(5, Math.max(1, level));
    document.body.setAttribute('data-font-size', String(fontSize));
    fontLevel.textContent = fontSize + ' de 5';
    decreaseFont.setAttribute('aria-disabled', String(fontSize === 1));
    increaseFont.setAttribute('aria-disabled', String(fontSize === 5));
    gravarStorage('alo-seguro-font-size', String(fontSize));
  }

  applyTheme(savedTheme === 'light' ? 'light' : 'dark');
  applyFontSize(fontSize);
  themeToggle.addEventListener('click', function () { applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'); });
  decreaseFont.addEventListener('click', function () { if (fontSize > 1) applyFontSize(fontSize - 1); });
  increaseFont.addEventListener('click', function () { if (fontSize < 5) applyFontSize(fontSize + 1); });

  // Cria elementos com segurança: texto vindo do servidor nunca vira HTML (evita XSS).
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

  var NOMES_CAMPOS = { email: 'e-mail', telefone: 'telefone' };
  function maiuscula(texto) { return texto.charAt(0).toUpperCase() + texto.slice(1); }

  var form = document.getElementById('scan-form');
  var submitBtn = document.getElementById('submit-btn');
  var scanBox = document.getElementById('scan-box');
  var resultBox = document.getElementById('result-box');
  var resetBtn = document.getElementById('reset-btn');
  var passos = { email: document.getElementById('step-email'), telefone: document.getElementById('step-telefone') };
  var notaFonte = document.getElementById('nota-fonte-texto');
  var erroContato = document.getElementById('err-contato');

  // ---------------------------------------------------------------------
  // Aviso sobre a fonte: pergunta ao servidor se está em modo demonstração.
  // ---------------------------------------------------------------------
  fetch(API_BASE + '/health')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (dados) {
      if (!dados || !dados.vazamentos) return;
      notaFonte.textContent = '';
      if (dados.vazamentos.demonstracao) {
        notaFonte.appendChild(el('strong', { texto: 'Modo demonstração: ' }));
        notaFonte.appendChild(document.createTextNode('o servidor usa uma base local com dados fictícios e não consulta a internet. ' +
          'Para ver um resultado positivo, use teste@exemplo.com ou o telefone (11) 99999-9999.'));
      } else {
        var fontes = dados.vazamentos.fontes.map(function (f) { return f.nome; }).join(', ');
        notaFonte.textContent = 'O servidor consulta: ' + fontes + '. Nenhuma chave de API fica no navegador.';
      }
      if (dados.vazamentos.aviso) notaFonte.appendChild(document.createTextNode(' ' + dados.vazamentos.aviso));
    })
    .catch(function () { /* sem servidor: o erro aparece ao enviar o formulário */ });

  // ---------------------------------------------------------------------
  // Validação (o servidor valida de novo; aqui é só para ajudar a pessoa)
  // ---------------------------------------------------------------------
  function onlyDigits(s) { return (s || '').replace(/\D/g, ''); }

  // aceita +55 / 55 na frente e devolve só DDD + número
  function normalizarTelefone(s) {
    var d = onlyDigits(s);
    if ((d.length === 12 || d.length === 13) && d.indexOf('55') === 0) d = d.slice(2);
    return d;
  }

  function setFieldState(inputId, errId, valid) {
    var input = document.getElementById(inputId);
    input.classList.toggle('invalid', !valid);
    input.setAttribute('aria-invalid', String(!valid));
    document.getElementById(errId).classList.toggle('show', !valid);
  }

  function limparErros() {
    setFieldState('f-email', 'err-email', true);
    setFieldState('f-telefone', 'err-telefone', true);
    erroContato.classList.remove('show');
  }

  function validate() {
    limparErros();
    var email = document.getElementById('f-email').value.trim();
    var telBruto = document.getElementById('f-telefone').value.trim();

    if (!email && !telBruto) {
      erroContato.classList.add('show');
      ['f-email', 'f-telefone'].forEach(function (id) {
        var input = document.getElementById(id);
        input.classList.add('invalid');
        input.setAttribute('aria-invalid', 'true');
      });
      return false;
    }
    var ok = true;
    if (email) {
      var emailValido = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
      setFieldState('f-email', 'err-email', emailValido);
      ok = ok && emailValido;
    }
    if (telBruto) {
      var tel = normalizarTelefone(telBruto);
      var telValido = tel.length === 10 || tel.length === 11;
      setFieldState('f-telefone', 'err-telefone', telValido);
      ok = ok && telValido;
    }
    return ok;
  }

  ['f-email', 'f-telefone'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', limparErros);
  });

  // ---------------------------------------------------------------------
  // Carregamento honesto: só marca "verificado" depois da resposta do servidor.
  // ---------------------------------------------------------------------
  function resetSteps() {
    Object.keys(passos).forEach(function (campo) {
      passos[campo].classList.remove('active', 'done', 'skipped');
      passos[campo].hidden = false;
      passos[campo].querySelector('.dot').textContent = '';
    });
  }

  function iniciarPassos(campos) {
    resetSteps();
    Object.keys(passos).forEach(function (campo) {
      passos[campo].hidden = campos.indexOf(campo) === -1;
      passos[campo].classList.add('active');
      passos[campo].querySelector('span').textContent = 'Consultando ' + NOMES_CAMPOS[campo] + ' nas fontes de vazamento…';
    });
  }

  function concluirPassos(dados) {
    Object.keys(passos).forEach(function (campo) {
      var passo = passos[campo];
      if (passo.hidden) return;
      passo.classList.remove('active');
      var dot = passo.querySelector('.dot');
      dot.textContent = '';
      if (dados && dados.campos_verificados.indexOf(campo) > -1) {
        passo.classList.add('done');
        dot.appendChild(icone('ti-check'));
        passo.querySelector('span').textContent = maiuscula(NOMES_CAMPOS[campo]) + ' verificado nas fontes disponíveis';
      } else {
        passo.classList.add('skipped');
        passo.querySelector('span').textContent = 'Não foi possível verificar o ' + NOMES_CAMPOS[campo];
      }
    });
  }

  // ---------------------------------------------------------------------
  // Resultado
  // ---------------------------------------------------------------------
  function abrirAnaliseDeMensagem(evento) {
    var aba = document.getElementById('aba-mensagem');
    if (!aba) return;
    evento.preventDefault();
    aba.click();
    aba.focus();
  }

  function linkDaRecomendacao(link) {
    if (!link) return null;
    if (link.url === '#analisar') {
      var interno = el('a', { href: '#analisar', 'class': 'rec-link', texto: link.texto });
      interno.addEventListener('click', abrirAnaliseDeMensagem);
      return interno;
    }
    if (!/^https:\/\//.test(link.url)) return null; // só links seguros do catálogo do servidor
    return el('a', { href: link.url, target: '_blank', rel: 'noopener noreferrer', 'class': 'rec-link' },
      [link.texto, el('span', { 'class': 'sr-only', texto: ' (abre em nova aba)' }), ' ', icone('ti-external-link')]);
  }

  function renderRecomendacoes(recomendacoes, titulo) {
    var lista = el('ol', { 'class': 'steps-list' });
    recomendacoes.forEach(function (rec, i) {
      lista.appendChild(el('li', {}, [
        el('span', { 'class': 'n', texto: String(i + 1) }),
        el('div', { 'class': 'rec' }, [
          el('strong', { 'class': 'rec-titulo', texto: rec.titulo }),
          el('span', { texto: rec.texto }),
          rec.por_que ? el('span', { 'class': 'rec-porque', texto: 'No seu caso: ' + rec.por_que }) : null,
          linkDaRecomendacao(rec.link)
        ])
      ]));
    });
    return [el('h3', { 'class': 'steps-title', texto: titulo }), lista];
  }

  function renderExposicao(exp) {
    var cabecalho = [el('strong', { texto: exp.incidente })];
    if (exp.data_formatada) cabecalho.push(el('span', { texto: exp.data_formatada }));
    var item = el('div', { 'class': 'leak-item' }, [
      el('div', { 'class': 'leak-item-head' }, cabecalho),
      el('div', { 'class': 'leak-item-row' }, [el('b', { texto: 'Dados expostos:' }), ' ' + (exp.dados_expostos.join(', ') || 'não informado')]),
      el('div', { 'class': 'leak-item-row' }, [el('b', { texto: 'Encontrado pelo:' }), ' ' + NOMES_CAMPOS[exp.campo]])
    ]);
    if (exp.dominio) item.appendChild(el('div', { 'class': 'leak-item-row' }, [el('b', { texto: 'Site:' }), ' ' + exp.dominio]));
    if (!exp.verificado) item.appendChild(el('div', { 'class': 'leak-item-row', texto: 'Incidente ainda não confirmado pela fonte.' }));
    return item;
  }

  function banner(classe, nomeIcone, titulo, texto) {
    return el('div', { 'class': 'result-banner ' + classe }, [icone(nomeIcone), el('div', {}, [
      el('h2', { tabindex: '-1', texto: titulo }),
      el('p', { texto: texto })
    ])]);
  }

  function render(dados, nome) {
    resultBox.textContent = '';
    var partes = [];
    var prefixo = nome ? nome + ', ' : '';

    if (dados.status === 'exposto') {
      var n = dados.exposicoes.length;
      partes.push(banner('leaked', 'ti-alert-triangle',
        prefixo + (nome ? 'encontramos ' : 'Encontramos ') + n + (n === 1 ? ' exposição' : ' exposições'), dados.resumo));
    } else if (dados.status === 'nada_encontrado') {
      partes.push(banner('clean', 'ti-shield-check',
        prefixo + (nome ? 'nada' : 'Nada') + ' encontrado nas fontes consultadas', dados.resumo));
    } else {
      partes.push(banner('unknown', 'ti-help-circle', 'Não foi possível verificar agora', dados.resumo));
    }

    if (dados.demonstracao) {
      partes.push(el('div', { 'class': 'aviso aviso-sistema', role: 'note' }, [icone('ti-flask'),
        el('span', { texto: 'Resultado de demonstração, com dados fictícios. Ele não indica se os seus dados reais vazaram.' })]));
    }
    (dados.avisos || []).forEach(function (aviso) {
      partes.push(el('div', { 'class': 'aviso aviso-sistema', role: 'note' }, [icone('ti-info-circle'), el('span', { texto: aviso })]));
    });

    dados.exposicoes.forEach(function (exp) { partes.push(renderExposicao(exp)); });

    if (dados.recomendacoes.length) {
      partes = partes.concat(renderRecomendacoes(dados.recomendacoes,
        dados.status === 'exposto' ? 'O que fazer agora' : 'Cuidados para continuar protegido'));
    }

    var fontes = (dados.fontes || []).map(function (f) { return f.nome; }).join(', ');
    var rodape = dados.aviso_limites;
    if (fontes) rodape += ' Fontes consultadas: ' + fontes + '.';
    if (dados.origem_resumo === 'ia') {
      rodape += ' O resumo e a ordem das recomendações foram feitos por IA (Google Gemini), que recebeu só o nome e a data ' +
        'dos incidentes e os tipos de dado, nunca o seu e-mail ou telefone.';
    }
    rodape += ' Não guardamos os dados consultados.';
    partes.push(el('p', { 'class': 'rodape-analise', texto: rodape }));

    partes.forEach(function (parte) { resultBox.appendChild(parte); });
  }

  function renderErro(mensagem) {
    resultBox.textContent = '';
    var aviso = banner('unknown', 'ti-plug-connected-x', 'Não conseguimos fazer a verificação', mensagem);
    aviso.setAttribute('role', 'alert');
    resultBox.appendChild(aviso);
  }

  // ---------------------------------------------------------------------
  // Envio
  // ---------------------------------------------------------------------
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!validate()) {
      var primeiroInvalido = form.querySelector('.invalid');
      if (primeiroInvalido) primeiroInvalido.focus();
      return;
    }

    var nome = document.getElementById('f-nome').value.trim().split(/\s+/)[0] || ''; // não sai do navegador
    var email = document.getElementById('f-email').value.trim();
    var tel = normalizarTelefone(document.getElementById('f-telefone').value);
    var corpo = {};
    if (email) corpo.email = email;
    if (tel) corpo.telefone = tel;

    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Verificando…';
    resultBox.classList.remove('show');
    resultBox.textContent = '';
    resetBtn.style.display = 'none';
    scanBox.classList.add('show');
    iniciarPassos(Object.keys(corpo));

    fetch(API_BASE + '/api/v1/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo)
    })
      .then(function (resposta) {
        return resposta.json().catch(function () { return {}; }).then(function (dados) {
          if (!resposta.ok) {
            throw new Error(typeof dados.detail === 'string' ? dados.detail : 'Não foi possível verificar agora. Tente de novo.');
          }
          return dados;
        });
      })
      .then(function (dados) {
        concluirPassos(dados);
        render(dados, nome);
      })
      .catch(function (falha) {
        concluirPassos(null);
        renderErro(falha instanceof TypeError
          ? 'Não conseguimos falar com o servidor do Alô Seguro. Ele está ligado? (veja "Como rodar" no README)'
          : falha.message);
      })
      .then(function () {
        resultBox.classList.add('show');
        var titulo = resultBox.querySelector('h2');
        if (titulo) titulo.focus();
        resetBtn.style.display = 'inline-flex';
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Verificar exposição';
      });
  });

  resetBtn.addEventListener('click', function () {
    form.reset();
    scanBox.classList.remove('show');
    resultBox.classList.remove('show');
    resultBox.textContent = '';
    resetSteps();
    limparErros();
    resetBtn.style.display = 'none';
    document.getElementById('f-email').focus();
  });
})();
