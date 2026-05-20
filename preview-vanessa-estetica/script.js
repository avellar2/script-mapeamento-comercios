(function() {
  'use strict';

  /* ---- Scroll Reveal ---- */
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('reveal--visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { root: null, rootMargin: '0px 0px -50px 0px', threshold: 0.08 }
  );

  document.querySelectorAll(
    '.section-header, .servico-item, .agendamento-box, .local-layout, .depoimento-card, .footer-grid > div, .hero-text, .hero-visual, .sobre-layout'
  ).forEach((el) => {
    el.classList.add('reveal');
    observer.observe(el);
  });

  /* ---- Navbar Scroll ---- */
  const nav = document.getElementById('nav');
  let lastScroll = 0;
  let ticking = false;

  function updateNav() {
    const y = window.scrollY || window.pageYOffset;
    nav.classList.toggle('nav--scrolled', y > 20);
    lastScroll = y;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateNav);
      ticking = true;
    }
  }, { passive: true });

  /* ---- Mobile Menu Toggle ---- */
  const navToggle = document.getElementById('navToggle');
  const navMobile = document.getElementById('navMobile');

  if (navToggle && navMobile) {
    navToggle.addEventListener('click', () => {
      navMobile.classList.toggle('nav-mobile--open');
    });

    navMobile.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        navMobile.classList.remove('nav-mobile--open');
      });
    });
  }

  /* ---- Smooth Scroll ---- */
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offset = (nav ? nav.offsetHeight : 0) + 16;
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /* ---- Hero Entrance ---- */
  const heroEls = document.querySelectorAll('.hero-badge, .hero-title, .hero-subtitle, .hero-actions, .hero-badges, .hero-person');
  heroEls.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = `opacity 700ms cubic-bezier(0.23,1,0.32,1) ${i * 100}ms, transform 700ms cubic-bezier(0.23,1,0.32,1) ${i * 100}ms`;
  });

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      heroEls.forEach((el) => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      });
    });
  });

  /* ================================================
     Modal de Agendamento
     ================================================ */
  const modal = document.getElementById('modalAgendamento');
  if (!modal) return; // modal logic below only runs if element exists

  const modalClose = document.getElementById('modalClose');
  const modalOverlay = modal.querySelector('.modal-overlay');
  const modalStepEl = document.getElementById('modalStep');
  const modalTitle = document.getElementById('modalTitle');
  const modalBack = document.getElementById('modalBack');
  const modalNext = document.getElementById('modalNext');
  const step1 = document.getElementById('step1');
  const step2 = document.getElementById('step2');
  const step3 = document.getElementById('step3');
  const modalDatas = document.getElementById('modalDatas');
  const modalHorarios = document.getElementById('modalHorarios');
  const resumoServico = document.getElementById('resumoServico');
  const resumoData = document.getElementById('resumoData');
  const resumoHorario = document.getElementById('resumoHorario');

  const servicosBtns = modal.querySelectorAll('.modal-servico');

  let currentStep = 1;
  let selectedServico = '';
  let selectedData = '';
  let selectedDataObj = null;
  let selectedHorario = '';

  const horarios = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00'];

  function openModal(preSelectedServico) {
    currentStep = 1;
    selectedServico = preSelectedServico || '';
    selectedData = '';
    selectedDataObj = null;
    selectedHorario = '';

    // Reset UI
    servicosBtns.forEach((btn) => {
      btn.classList.toggle('selected', btn.dataset.servico === selectedServico);
    });
    if (modalDatas) modalDatas.innerHTML = '';
    if (modalHorarios) modalHorarios.innerHTML = '';

    renderStep();
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function renderStep() {
    step1.hidden = currentStep !== 1;
    step2.hidden = currentStep !== 2;
    step3.hidden = currentStep !== 3;

    modalStepEl.textContent = `Passo ${currentStep} de 3`;
    modalBack.hidden = currentStep === 1;

    if (currentStep === 1) {
      modalTitle.textContent = 'Escolha o servico';
      modalNext.textContent = 'Proximo';
      modalNext.disabled = !selectedServico;
    } else if (currentStep === 2) {
      modalTitle.textContent = 'Escolha data e horario';
      modalNext.textContent = 'Proximo';
      modalNext.disabled = !(selectedData && selectedHorario);
      if (modalDatas && !modalDatas.hasChildNodes()) gerarDatas();
      if (modalHorarios && !modalHorarios.hasChildNodes()) gerarHorarios();
    } else if (currentStep === 3) {
      modalTitle.textContent = 'Confirme seu agendamento';
      modalNext.textContent = 'Confirmar e ir para o WhatsApp';
      modalNext.disabled = false;
      resumoServico.textContent = selectedServico;
      resumoData.textContent = selectedData;
      resumoHorario.textContent = selectedHorario;
    }
  }

  function gerarDatas() {
    modalDatas.innerHTML = '';
    const hoje = new Date();
    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'];

    for (let i = 1; i <= 14; i++) {
      const d = new Date(hoje);
      d.setDate(hoje.getDate() + i);
      if (d.getDay() === 0) continue; // pula domingo

      const diaLabel = diasSemana[d.getDay()];
      const diaNum = String(d.getDate()).padStart(2, '0');
      const mesNum = String(d.getMonth() + 1).padStart(2, '0');
      const dataStr = `${diaNum}/${mesNum}`;
      const iso = d.toISOString().split('T')[0];

      const btn = document.createElement('button');
      btn.className = 'modal-data';
      btn.type = 'button';
      btn.innerHTML = `<span>${diaLabel}</span><span>${diaNum}</span>`;
      btn.dataset.data = dataStr;
      btn.dataset.iso = iso;
      btn.dataset.diaSemana = diaLabel;

      btn.addEventListener('click', () => {
        modalDatas.querySelectorAll('.modal-data').forEach((b) => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedData = `${diaLabel}, ${dataStr}`;
        selectedDataObj = d;
        modalNext.disabled = !(selectedData && selectedHorario);
      });

      modalDatas.appendChild(btn);
    }
  }

  function gerarHorarios() {
    modalHorarios.innerHTML = '';
    horarios.forEach((h) => {
      const btn = document.createElement('button');
      btn.className = 'modal-horario';
      btn.type = 'button';
      btn.textContent = h;

      btn.addEventListener('click', () => {
        modalHorarios.querySelectorAll('.modal-horario').forEach((b) => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedHorario = h;
        modalNext.disabled = !(selectedData && selectedHorario);
      });

      modalHorarios.appendChild(btn);
    });
  }

  // Triggers de abertura
  document.querySelectorAll('.servico-item').forEach((card) => {
    card.addEventListener('click', () => {
      openModal(card.dataset.servico);
    });
  });

  const heroAgendar = document.getElementById('heroAgendar');
  if (heroAgendar) {
    heroAgendar.addEventListener('click', () => openModal());
  }

  const btnAbrirModal = document.getElementById('btnAbrirModal');
  if (btnAbrirModal) {
    btnAbrirModal.addEventListener('click', () => openModal());
  }

  // Fechar
  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') {
      closeModal();
    }
  });

  // Selecionar servico no modal
  servicosBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      servicosBtns.forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedServico = btn.dataset.servico;
      modalNext.disabled = false;
    });
  });

  // Navegacao
  modalBack.addEventListener('click', () => {
    if (currentStep > 1) {
      currentStep--;
      renderStep();
    }
  });

  modalNext.addEventListener('click', () => {
    if (currentStep < 3) {
      currentStep++;
      renderStep();
    } else {
      // Confirmar -> WhatsApp
      const phone = '5521999999999';
      let msg = `Ola, vim pela pagina da Vanessa Sgrancio Estetica e gostaria de agendar.`;
      msg += `%0A%0A*Servico:* ${selectedServico}`;
      msg += `%0A*Data:* ${selectedData}`;
      msg += `%0A*Horario:* ${selectedHorario}`;
      msg += `%0A%0APode confirmar esse agendamento?`;
      window.open(`https://wa.me/${phone}?text=${msg}`, '_blank');
      closeModal();
    }
  });
})();
