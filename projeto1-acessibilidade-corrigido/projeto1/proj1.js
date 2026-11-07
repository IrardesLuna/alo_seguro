(function () {
  // ---------------------------------------------------------------------
  // Base local de DEMONSTRAÇÃO apenas. Em produção, substitua checkLeaks()
  // por uma chamada ao SEU backend, que por sua vez consulta uma API real
  // de vazamentos (ex.: Have I Been Pwned) usando uma chave de API mantida
  // em segredo no servidor — nunca no código do navegador.
  // ---------------------------------------------------------------------
  'use strict';

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
  var DEMO_DB = {
    emails: {
      'teste@exemplo.com': [
        { dado: 'E-mail e senha (hash)', fonte: 'Vazamento "ColecaoDados2021"', data: 'jan. 2021' },
        { dado: 'Nome completo e telefone', fonte: 'Vazamento de loja on-line fictícia "LojaExemplo"', data: 'jun. 2023' }
      ]
    },
    telefones: {
      '11999999999': [
        { dado: 'Telefone e nome completo', fonte: 'Vazamento de rede social fictícia "RedeExemplo"', data: 'ago. 2022' }
      ]
    }
  };

  var form = document.getElementById('scan-form');
  var submitBtn = document.getElementById('submit-btn');
  var scanBox = document.getElementById('scan-box');
  var resultBox = document.getElementById('result-box');
  var resetBtn = document.getElementById('reset-btn');
  var step1 = document.getElementById('step-1');
  var step2 = document.getElementById('step-2');

  function onlyDigits(s) { return (s || '').replace(/\D/g, ''); }

  // aceita +55 / 55 na frente e devolve só DDD + número
  function normalizarTelefone(s) {
    var d = onlyDigits(s);
    if ((d.length === 12 || d.length === 13) && d.indexOf('55') === 0) d = d.slice(2);
    return d;
  }

  function resetSteps() {
    [step1, step2].forEach(function (s) {
      s.classList.remove('active', 'done');
      s.querySelector('.dot').innerHTML = '';
    });
  }

  function validate() {
    var ok = true;
    var nome = document.getElementById('f-nome').value.trim();
    var email = document.getElementById('f-email').value.trim();
    var tel = normalizarTelefone(document.getElementById('f-telefone').value);

    var nomeValido = nome.length > 3 && nome.indexOf(' ') > -1;
    setFieldState('f-nome', 'err-nome', nomeValido);
    ok = ok && nomeValido;

    var emailValido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    setFieldState('f-email', 'err-email', emailValido);
    ok = ok && emailValido;

    var telValido = tel.length === 10 || tel.length === 11;
    setFieldState('f-telefone', 'err-telefone', telValido);
    ok = ok && telValido;

    return ok;
  }

  function setFieldState(inputId, errId, valid) {
    var input = document.getElementById(inputId);
    var err = document.getElementById(errId);
    input.classList.toggle('invalid', !valid);
    input.setAttribute('aria-invalid', String(!valid));
    err.classList.toggle('show', !valid);
  }

  ['f-nome', 'f-email', 'f-telefone'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', function () {
      this.classList.remove('invalid');
      this.setAttribute('aria-invalid', 'false');
      document.getElementById('err-' + id.split('-')[1]).classList.remove('show');
    });
  });

  function checkLeaks(email, telDigits) {
    var achados = [];
    var emailAchados = DEMO_DB.emails[email.toLowerCase()];
    var telAchados = DEMO_DB.telefones[telDigits];
    if (emailAchados) achados = achados.concat(emailAchados);
    if (telAchados) achados = achados.concat(telAchados);
    return achados;
  }

  function renderLeaked(achados) {
    var html = '';
    html += '<div class="result-banner leaked"><i class="ti ti-alert-triangle" aria-hidden="true"></i><div>' +
      '<h2>Encontramos ' + achados.length + (achados.length === 1 ? ' exposição' : ' exposições') + '</h2>' +
      '<p>Seus dados aparecem em pelo menos um vazamento conhecido. Veja os detalhes e siga as recomendações abaixo.</p></div></div>';

    achados.forEach(function (a) {
      html += '<div class="leak-item">' +
        '<div class="leak-item-head"><strong>' + a.fonte + '</strong><span>' + a.data + '</span></div>' +
        '<div class="leak-item-row"><b>Dado exposto:</b> ' + a.dado + '</div>' +
        '</div>';
    });

    html += '<div class="steps-title">O que fazer agora</div>';
    html += '<ol class="steps-list">' +
      '<li><span class="n">1</span><span>Trocar senhas imediatamente, principalmente se você usa a mesma senha em outros sites.</span></li>' +
      '<li><span class="n">2</span><span>Ativar autenticação de dois fatores (2FA) nas contas afetadas.</span></li>' +
      '<li><span class="n">3</span><span>Monitorar contas financeiras (converse com o gerente do seu banco).</span></li>' +
      '<li><span class="n">4</span><span>Registrar Boletim de Ocorrência.</span></li>' +
      '<li><span class="n">5</span><span>Denunciar no canal apropriado — para dados pessoais, a ANPD; para golpes financeiros, o seu banco e a Polícia Civil.</span></li>' +
      '</ol>';

    resultBox.innerHTML = html;
  }

  function renderClean() {
    resultBox.innerHTML =
      '<div class="result-banner clean"><i class="ti ti-shield-check" aria-hidden="true"></i><div>' +
      '<h2>Nada encontrado nas bases verificadas</h2>' +
      '<p>Não localizamos seu e-mail ou telefone em vazamentos conhecidos até o momento. Isso pode mudar, então vale manter esses cuidados:</p></div></div>' +
      '<ul class="tips-list">' +
      '<li><i class="ti ti-key" aria-hidden="true"></i><span>Use senhas únicas e longas para cada site — um gerenciador de senhas ajuda bastante.</span></li>' +
      '<li><i class="ti ti-lock-2" aria-hidden="true"></i><span>Ative a autenticação de dois fatores (2FA) sempre que disponível.</span></li>' +
      '<li><i class="ti ti-mail-off" aria-hidden="true"></i><span>Desconfie de e-mails e mensagens pedindo dados pessoais ou financeiros, mesmo que pareçam oficiais.</span></li>' +
      '<li><i class="ti ti-refresh" aria-hidden="true"></i><span>Verifique periodicamente se seus dados apareceram em novos vazamentos.</span></li>' +
      '<li><i class="ti ti-credit-card-off" aria-hidden="true"></i><span>Nunca informe número de cartão ou dados bancários completos para "verificar" vazamentos — nenhum serviço legítimo pede isso.</span></li>' +
      '</ul>';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!validate()) {
      var primeiroInvalido = form.querySelector('.invalid');
      if (primeiroInvalido) primeiroInvalido.focus();
      return;
    }

    var email = document.getElementById('f-email').value.trim();
    var tel = normalizarTelefone(document.getElementById('f-telefone').value);

    submitBtn.disabled = true;
    scanBox.classList.add('show');
    resultBox.classList.remove('show');
    resultBox.innerHTML = '';
    resetSteps();
    step1.classList.add('active');

    setTimeout(function () {
      step1.classList.remove('active');
      step1.classList.add('done');
      step1.querySelector('.dot').innerHTML = '<i class="ti ti-check" aria-hidden="true"></i>';
      step2.classList.add('active');
    }, 650);

    setTimeout(function () {
      step2.classList.remove('active');
      step2.classList.add('done');
      step2.querySelector('.dot').innerHTML = '<i class="ti ti-check" aria-hidden="true"></i>';

      var achados = checkLeaks(email, tel);
      if (achados.length > 0) {
        renderLeaked(achados);
      } else {
        renderClean();
      }
      resultBox.classList.add('show');
      var titulo = resultBox.querySelector('h2');
      if (titulo) { titulo.setAttribute('tabindex', '-1'); titulo.focus(); }
      resetBtn.style.display = 'inline-flex';
      submitBtn.disabled = false;
    }, 1300);
  });

  resetBtn.addEventListener('click', function () {
    form.reset();
    scanBox.classList.remove('show');
    resultBox.classList.remove('show');
    resultBox.innerHTML = '';
    resetSteps();
    resetBtn.style.display = 'none';
    ['f-nome', 'f-email', 'f-telefone'].forEach(function (id) {
      var el = document.getElementById(id);
      el.classList.remove('invalid');
      el.setAttribute('aria-invalid', 'false');
      document.getElementById('err-' + id.split('-')[1]).classList.remove('show');
    });
    document.getElementById('f-nome').focus();
  });
})();
