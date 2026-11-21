(function () {
  // -----------------------------------------------------------------------
  // Aba "Tirar dúvidas": chat sobre golpes e phishing (POST /api/v1/conversa).
  // O histórico fica só na memória desta página e é enviado a cada pergunta:
  // o servidor não guarda nada, e tudo some ao fechar ou recarregar a página.
  // -----------------------------------------------------------------------
  'use strict';

  var API_BASE = window.ALO_SEGURO_API_BASE !== undefined ? window.ALO_SEGURO_API_BASE
    : (location.protocol === 'file:' || location.port === '5500' || location.port === '5501') ? 'http://127.0.0.1:8000' : '';

  var BOAS_VINDAS = 'Olá! Eu ajudo você a descobrir se uma mensagem, ligação ou pedido é golpe, e explico o que fazer. ' +
    'Pode escrever do seu jeito ou tocar em uma das perguntas abaixo.';
  var SUGESTOES_INICIAIS = ['Recebi uma mensagem estranha', 'Acho que caí em um golpe', 'Como saber se um link é seguro?'];
  var SUGESTOES_DA_ANALISE = ['Por que isso parece golpe?', 'Já cliquei ou paguei. E agora?', 'Como confirmo se é verdade?'];
  var NIVEIS = {
    baixo: 'Risco baixo', medio: 'Risco médio', alto: 'Risco alto', muito_alto: 'Risco muito alto'
  };

  var lista = document.getElementById('conversa-mensagens');
  var pensando = document.getElementById('conversa-pensando');
  var sugestoesBox = document.getElementById('conversa-sugestoes');
  var form = document.getElementById('conversa-form');
  var campo = document.getElementById('f-conversa');
  var botao = document.getElementById('conversa-enviar');
  var erro = document.getElementById('err-conversa');
  var restantes = document.getElementById('conversa-restantes');
  var contextoBox = document.getElementById('conversa-contexto');
  var nova = document.getElementById('conversa-nova');
  if (!lista || !form) return;

  var historico = [];      // [{papel: 'usuario'|'assistente', texto}] — enviado ao servidor
  var contexto = null;     // resumo da análise de mensagem, quando a conversa começa por lá
  var enviando = false;
  var podeFalar = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

  // Cria elementos com segurança: texto vindo da IA nunca vira HTML (evita XSS).
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

  // Linhas começando com "- " viram lista; o resto vira parágrafo.
  function textoFormatado(texto) {
    var bloco = el('div', { 'class': 'balao-texto' });
    var listaAtual = null;
    texto.split('\n').forEach(function (linha) {
      linha = linha.trim();
      if (!linha) { listaAtual = null; return; }
      if (/^[-•*]\s+/.test(linha)) {
        if (!listaAtual) { listaAtual = el('ul'); bloco.appendChild(listaAtual); }
        listaAtual.appendChild(el('li', { texto: linha.replace(/^[-•*]\s+/, '') }));
      } else {
        listaAtual = null;
        bloco.appendChild(el('p', { texto: linha }));
      }
    });
    return bloco;
  }

  // ---------------------------------------------------------------------
  // Ouvir a resposta (voz do próprio navegador, sem IA e sem internet)
  // ---------------------------------------------------------------------
  var botaoFalando = null;

  function pararFala() {
    if (!podeFalar) return;
    window.speechSynthesis.cancel();
    if (botaoFalando) {
      botaoFalando.setAttribute('aria-pressed', 'false');
      botaoFalando.querySelector('span').textContent = 'Ouvir resposta';
      botaoFalando = null;
    }
  }

  function botaoOuvir(texto) {
    if (!podeFalar) return null;
    var b = el('button', { type: 'button', 'class': 'btn-ouvir', 'aria-pressed': 'false' }, [icone('ti-volume'), el('span', { texto: 'Ouvir resposta' })]);
    b.addEventListener('click', function () {
      var estavaFalando = botaoFalando === b;
      pararFala();
      if (estavaFalando) return;
      var fala = new SpeechSynthesisUtterance(texto.replace(/^[-•*]\s+/gm, '').replace(/\[[^\]]+\]/g, ''));
      fala.lang = 'pt-BR';
      fala.rate = 0.95;
      var vozes = window.speechSynthesis.getVoices().filter(function (v) { return /^pt(-|_)BR/i.test(v.lang); });
      if (vozes.length) fala.voice = vozes[0];
      fala.onend = function () { if (botaoFalando === b) pararFala(); };
      botaoFalando = b;
      b.setAttribute('aria-pressed', 'true');
      b.querySelector('span').textContent = 'Parar de ouvir';
      window.speechSynthesis.speak(fala);
    });
    return b;
  }

  // ---------------------------------------------------------------------
  // Mensagens na tela
  // ---------------------------------------------------------------------
  function rolarParaFim() { lista.lastElementChild && lista.lastElementChild.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }

  function adicionarDaPessoa(texto) {
    var item = el('li', { 'class': 'balao balao-pessoa' }, [
      el('span', { 'class': 'sr-only', texto: 'Você disse: ' }),
      textoFormatado(texto)
    ]);
    lista.appendChild(item);
    rolarParaFim();
    return item;
  }

  function adicionarDoAssistente(dados) {
    var filhos = [el('span', { 'class': 'balao-autor', texto: 'Alô Seguro' })];
    if (dados.nivel_risco && NIVEIS[dados.nivel_risco]) {
      filhos.push(el('div', { 'class': 'nivel-' + dados.nivel_risco }, [el('span', { 'class': 'selo-nivel', texto: NIVEIS[dados.nivel_risco] })]));
    }
    filhos.push(textoFormatado(dados.resposta));
    if (dados.aviso_ajuda) {
      filhos.push(el('div', { 'class': 'aviso aviso-ajuda', role: 'note' }, [
        icone('ti-lifebuoy'), el('div', {}, [el('strong', { texto: 'Você não está sozinho. Procure ajuda: ' }), dados.aviso_ajuda])
      ]));
    }
    if (dados.aviso_sistema) {
      filhos.push(el('p', { 'class': 'balao-nota', texto: dados.aviso_sistema }));
    } else if (dados.dados_ocultados > 0) {
      filhos.push(el('p', { 'class': 'balao-nota', texto: 'Ocultamos ' + dados.dados_ocultados + (dados.dados_ocultados === 1 ? ' dado pessoal' : ' dados pessoais') + ' da sua mensagem antes de analisar.' }));
    }
    filhos.push(botaoOuvir(dados.resposta));
    lista.appendChild(el('li', { 'class': 'balao balao-assistente' }, filhos));
    rolarParaFim();
  }

  function mostrarSugestoes(sugestoes) {
    sugestoesBox.textContent = '';
    (sugestoes || []).forEach(function (texto) {
      var b = el('button', { type: 'button', 'class': 'sugestao' }, [texto]);
      b.addEventListener('click', function () { enviar(texto); });
      sugestoesBox.appendChild(b);
    });
  }

  function atualizarRestantes(n) {
    if (n === null || n === undefined) { restantes.textContent = ''; return; }
    restantes.textContent = n === 1 ? 'Resta 1 pergunta nesta conversa' : 'Restam ' + n + ' perguntas nesta conversa';
    if (n <= 0) {
      restantes.textContent = 'Limite desta conversa atingido';
      campo.disabled = true;
      botao.disabled = true;
      mostrarSugestoes([]);
      lista.appendChild(el('li', { 'class': 'balao balao-sistema', texto: 'Esta conversa chegou ao limite de perguntas. Toque em "Começar nova conversa" para continuar.' }));
    }
  }

  function mostrarErro(mensagem) {
    erro.textContent = mensagem;
    erro.classList.add('show');
    campo.setAttribute('aria-invalid', 'true');
  }

  function limparErro() {
    erro.classList.remove('show');
    erro.textContent = '';
    campo.setAttribute('aria-invalid', 'false');
  }

  function definirEnviando(ativo) {
    enviando = ativo;
    botao.disabled = ativo;
    botao.querySelector('span').textContent = ativo ? 'Enviando…' : 'Enviar';
    pensando.hidden = !ativo;
    Array.prototype.forEach.call(sugestoesBox.querySelectorAll('button'), function (b) { b.disabled = ativo; });
  }

  // ---------------------------------------------------------------------
  // Envio
  // ---------------------------------------------------------------------
  function enviar(texto) {
    texto = (texto || '').trim();
    if (enviando || campo.disabled) return;
    if (!texto) { mostrarErro('Escreva sua dúvida ou toque em uma das perguntas.'); campo.focus(); return; }

    limparErro();
    pararFala();
    var balao = adicionarDaPessoa(texto);
    historico.push({ papel: 'usuario', texto: texto });
    campo.value = '';
    definirEnviando(true);

    fetch(API_BASE + '/api/v1/conversa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ historico: historico, contexto: contexto })
    })
      .then(function (resposta) {
        return resposta.json().catch(function () { return {}; }).then(function (corpo) {
          if (!resposta.ok) throw new Error(typeof corpo.detail === 'string' ? corpo.detail : 'Não foi possível responder agora. Tente de novo.');
          return corpo;
        });
      })
      .then(function (dados) {
        historico.push({ papel: 'assistente', texto: dados.resposta });
        adicionarDoAssistente(dados);
        mostrarSugestoes(dados.sugestoes);
        definirEnviando(false);
        atualizarRestantes(dados.perguntas_restantes);
        if (!campo.disabled) campo.focus();
      })
      .catch(function (falha) {
        // Desfaz a pergunta para a pessoa poder tentar de novo sem digitar tudo outra vez.
        historico.pop();
        balao.remove();
        campo.value = texto;
        definirEnviando(false);
        mostrarErro(falha instanceof TypeError
          ? 'Não conseguimos falar com o servidor do Alô Seguro. Ele está ligado? (veja "Como rodar" no README)'
          : falha.message);
        campo.focus();
      });
  }

  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    enviar(campo.value);
  });

  campo.addEventListener('keydown', function (evento) {
    if (evento.key === 'Enter' && !evento.shiftKey && !evento.isComposing) {
      evento.preventDefault();
      enviar(campo.value);
    }
  });
  campo.addEventListener('input', limparErro);

  function reiniciar(novoContexto) {
    pararFala();
    historico = [];
    contexto = novoContexto || null;
    lista.textContent = '';
    campo.disabled = false;
    campo.value = '';
    botao.disabled = false;
    limparErro();
    atualizarRestantes(null);

    contextoBox.textContent = '';
    contextoBox.hidden = !contexto;
    if (contexto) {
      var resumo = (NIVEIS[contexto.nivel] || 'Análise') + (contexto.probabilidade_golpe ? ' (' + contexto.probabilidade_golpe + '% de chance de golpe)' : '');
      contextoBox.appendChild(icone('ti-link'));
      contextoBox.appendChild(el('span', {}, [el('strong', { texto: 'Conversando sobre a mensagem que você analisou: ' }), resumo + (contexto.veredito ? '. ' + contexto.veredito : '')]));
    }

    var boasVindas = contexto
      ? 'Vamos conversar sobre a mensagem que você analisou. O que você quer saber?'
      : BOAS_VINDAS;
    lista.appendChild(el('li', { 'class': 'balao balao-assistente' }, [
      el('span', { 'class': 'balao-autor', texto: 'Alô Seguro' }), textoFormatado(boasVindas), botaoOuvir(boasVindas)
    ]));
    mostrarSugestoes(contexto ? SUGESTOES_DA_ANALISE : SUGESTOES_INICIAIS);
  }

  nova.addEventListener('click', function () { reiniciar(null); campo.focus(); });

  // Usado por analisar.js: "Tirar dúvidas sobre esta análise".
  window.AloSeguroConversa = {
    abrirComAnalise: function (resumoDaAnalise) {
      reiniciar(resumoDaAnalise);
      var aba = document.getElementById('aba-conversa');
      if (aba) aba.click();
      campo.focus();
    }
  };

  reiniciar(null);
})();
