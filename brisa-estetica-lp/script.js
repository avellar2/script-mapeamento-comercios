(function() {
  'use strict';

  /* ---- Scroll Reveal ---- */
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { root: null, rootMargin: '0px 0px -50px 0px', threshold: 0.08 }
  );

  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

  /* ---- Navbar Scroll ---- */
  const header = document.getElementById('header');
  let lastScroll = 0;
  let ticking = false;

  function updateHeader() {
    const y = window.scrollY || window.pageYOffset;
    header.classList.toggle('scrolled', y > 20);
    lastScroll = y;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateHeader);
      ticking = true;
    }
  }, { passive: true });

  /* ---- Mobile Menu ---- */
  const menuToggle = document.getElementById('menuToggle');
  const nav = document.getElementById('nav');

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      menuToggle.classList.toggle('active');
      nav.classList.toggle('open');
    });

    nav.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        menuToggle.classList.remove('active');
        nav.classList.remove('open');
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
        const offset = (header ? header.offsetHeight : 0) + 16;
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /* ---- Hero Entrance Animation ---- */
  const heroEls = document.querySelectorAll('.hero-badge, .hero-title, .hero-desc, .hero-actions, .hero-badges, .hero-visual');
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
     Modal de Agendamento - 3 Passos
     ================================================ */
  const modal = document.getElementById('modalAgendamento');
  if (!modal) return;

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
  let selectedHorario = '';

  const horarios = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00'];

  function openModal(preSelectedServico) {
    currentStep = 1;
    selectedServico = preSelectedServico || '';
    selectedData = '';
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
      modalTitle.textContent = 'Escolha o serviço';
      modalNext.textContent = 'Próximo';
      modalNext.disabled = !selectedServico;
    } else if (currentStep === 2) {
      modalTitle.textContent = 'Escolha data e horário';
      modalNext.textContent = 'Próximo';
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
    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

    for (let i = 1; i <= 14; i++) {
      const d = new Date(hoje);
      d.setDate(hoje.getDate() + i);
      if (d.getDay() === 0) continue; // pula domingo

      const diaLabel = diasSemana[d.getDay()];
      const diaNum = String(d.getDate()).padStart(2, '0');
      const mesNum = String(d.getMonth() + 1).padStart(2, '0');
      const dataStr = `${diaNum}/${mesNum}`;

      const btn = document.createElement('button');
      btn.className = 'modal-data';
      btn.type = 'button';
      btn.innerHTML = `<span>${diaLabel}</span><span>${diaNum}</span>`;
      btn.dataset.data = dataStr;

      btn.addEventListener('click', () => {
        modalDatas.querySelectorAll('.modal-data').forEach((b) => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedData = `${diaLabel}, ${dataStr}`;
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

  const btnAgendarHeader = document.getElementById('btnAgendarHeader');
  if (btnAgendarHeader) {
    btnAgendarHeader.addEventListener('click', () => openModal());
  }

  // Fechar modal
  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') {
      closeModal();
    }
  });

  // Selecionar serviço no modal
  servicosBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      servicosBtns.forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedServico = btn.dataset.servico;
      modalNext.disabled = false;
    });
  });

  // Navegação
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
      const phone = '55219999999999';
      let msg = `Olá! Vim pela página da Brisa Estética Holística e gostaria de agendar.`;
      msg += `%0A%0A*Serviço:* ${selectedServico}`;
      msg += `%0A*Data:* ${selectedData}`;
      msg += `%0A*Horário:* ${selectedHorario}`;
      msg += `%0A%0APode confirmar esse agendamento?`;
      window.open(`https://wa.me/${phone}?text=${msg}`, '_blank');
      closeModal();
    }
  });
})();
