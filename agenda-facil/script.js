const business = {
  name: 'Barbearia do João',
  phone: '5521999999999',
  slots: ['09:00','10:00','11:00','14:00','15:00','16:00','17:00','18:00']
};

const categories = [
  {
    name: 'Cortes',
    services: [
      {
        id: 1,
        name: 'Corte Masculino',
        duration: '45 min',
        price: 35,
        description: 'Corte moderno com acabamento profissional e finalização.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>`
      },
      {
        id: 5,
        name: 'Degradê Navalhado',
        duration: '50 min',
        price: 40,
        description: 'Degradê preciso com acabamento de navalhete.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.2 7.8l-6.8 6.8"/><path d="M3.8 16.2l6.8-6.8"/><circle cx="12" cy="12" r="10" opacity="0.2"/><path d="M6 3l6 6"/><path d="M18 3l-6 6"/></svg>`
      }
    ]
  },
  {
    name: 'Barba & Acabamentos',
    services: [
      {
        id: 2,
        name: 'Barba',
        duration: '30 min',
        price: 25,
        description: 'Barba alinhada com toalha quente e produtos.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 11v6a4 4 0 0 0 8 0v-6"/><path d="M6 8h12"/><path d="M6 8c0-3.3 2.7-6 6-6s6 2.7 6 6"/></svg>`
      },
      {
        id: 4,
        name: 'Sobrancelha',
        duration: '15 min',
        price: 15,
        description: 'Design rápido para acabamento do rosto.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-4 10-4 10 4 10 4"/><path d="M2 12s4 4 10 4 10-4 10-4"/></svg>`
      },
      {
        id: 6,
        name: 'Pezinho',
        duration: '10 min',
        price: 10,
        description: 'Acabamento na nuca para manter o corte alinhado.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M2 12h20"/></svg>`
      }
    ]
  },
  {
    name: 'Combos',
    services: [
      {
        id: 3,
        name: 'Corte + Barba',
        duration: '1h',
        price: 55,
        description: 'Combo completo para renovar o visual.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`
      },
      {
        id: 7,
        name: 'Corte + Barba + Sobrancelha',
        duration: '1h 15min',
        price: 65,
        description: 'O pacote completo de cuidados masculinos.',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`
      }
    ]
  }
];

const state = {
  step: 1,
  selectedService: null,
  selectedDate: '',
  selectedTime: '',
  name: '',
  phone: '',
  note: ''
};

const servicesList = document.getElementById('servicesList');
const searchInput = document.getElementById('searchInput');
const searchWrap = document.getElementById('searchWrap');
const timeGrid = document.getElementById('timeGrid');
const dateInput = document.getElementById('dateInput');
const dateField = document.getElementById('dateField');
const dateDisplay = document.getElementById('dateDisplay');
const dateError = document.getElementById('dateError');
const timeError = document.getElementById('timeError');
const clientName = document.getElementById('clientName');
const clientPhone = document.getElementById('clientPhone');
const clientNote = document.getElementById('clientNote');
const nameError = document.getElementById('nameError');
const phoneError = document.getElementById('phoneError');
const nameGroup = document.getElementById('nameGroup');
const phoneGroup = document.getElementById('phoneGroup');
const backBtn = document.getElementById('backBtn');
const nextBtn = document.getElementById('nextBtn');
const stepPanels = document.querySelectorAll('.step-panel');
const stepperSteps = document.querySelectorAll('.stepper-step');
const stepperLines = document.querySelectorAll('.stepper-line');
const receiptService = document.getElementById('receiptService');
const receiptDate = document.getElementById('receiptDate');
const receiptTime = document.getElementById('receiptTime');
const receiptPrice = document.getElementById('receiptPrice');
const whatsappBtn = document.getElementById('whatsappBtn');
const myBookingsBtn = document.getElementById('myBookingsBtn');
const modalOverlay = document.getElementById('modalOverlay');
const modalClose = document.getElementById('modalClose');
const modalBody = document.getElementById('modalBody');

function init() {
  renderServices();
  setupListeners();
  updateUI();
  const today = new Date().toISOString().split('T')[0];
  dateInput.min = today;
}

function getAllServices() {
  return categories.flatMap(c => c.services);
}

function renderServices(filter = '') {
  const term = filter.toLowerCase().trim();
  const filtered = categories.map(cat => {
    const services = term
      ? cat.services.filter(s =>
          s.name.toLowerCase().includes(term) ||
          s.description.toLowerCase().includes(term)
        )
      : cat.services;
    return { ...cat, services };
  }).filter(cat => cat.services.length > 0);

  if (filtered.length === 0) {
    servicesList.innerHTML = `<p class="modal-empty" style="padding:2rem 0">Nenhum serviço encontrado.</p>`;
    return;
  }

  servicesList.innerHTML = filtered.map((cat, catIdx) => {
    const isOpen = term ? 'open' : (catIdx === 0 ? 'open' : '');
    return `
      <div class="accordion ${isOpen}" data-cat="${cat.name}">
        <button type="button" class="accordion-header">
          ${cat.name}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </button>
        <div class="accordion-body">
          <div class="accordion-inner">
            <div class="accordion-content">
              ${cat.services.map(s => serviceItemHTML(s)).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  servicesList.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      header.closest('.accordion').classList.toggle('open');
    });
  });

  servicesList.querySelectorAll('.service-item').forEach(item => {
    item.addEventListener('click', (e) => {
      if (e.target.closest('.btn-select')) {
        selectService(Number(item.dataset.id));
        return;
      }
      selectService(Number(item.dataset.id));
    });
  });
}

function serviceItemHTML(s) {
  const isSelected = state.selectedService && state.selectedService.id === s.id;
  return `
    <div class="service-item ${isSelected ? 'selected' : ''}" data-id="${s.id}" role="button" tabindex="0" aria-pressed="${isSelected}">
      <div class="service-radio"></div>
      <div class="service-thumb-placeholder">${s.icon}</div>
      <div class="service-info">
        <div class="service-name">${s.name}</div>
        <div class="service-desc">${s.description}</div>
        <div class="service-meta">${s.duration} — ${formatCurrency(s.price)}</div>
      </div>
      <button type="button" class="btn-select">${isSelected ? 'Selecionado' : 'Selecionar'}</button>
    </div>
  `;
}

function selectService(id) {
  state.selectedService = getAllServices().find(s => s.id === id) || null;
  renderServices(searchInput.value);
  clearErrors();
}

function renderTimeSlots() {
  const bookings = getBookings();
  const booked = bookings
    .filter(b => b.date === state.selectedDate)
    .map(b => b.time);

  timeGrid.innerHTML = business.slots.map(time => {
    const disabled = booked.includes(time);
    const selected = state.selectedTime === time && !disabled;
    return `<button type="button" class="time-slot ${selected ? 'selected' : ''}" data-time="${time}" ${disabled ? 'disabled' : ''}>${time}</button>`;
  }).join('');

  timeGrid.querySelectorAll('.time-slot:not(:disabled)').forEach(btn => {
    btn.addEventListener('click', () => {
      state.selectedTime = btn.dataset.time;
      timeError.textContent = '';
      renderTimeSlots();
    });
  });
}

function setupListeners() {
  nextBtn.addEventListener('click', handleNext);
  backBtn.addEventListener('click', handleBack);

  searchInput.addEventListener('input', () => {
    renderServices(searchInput.value);
  });

  dateInput.addEventListener('input', () => {
    state.selectedDate = dateInput.value;
    dateError.textContent = '';
    dateField.classList.remove('has-error');
  });

  clientName.addEventListener('input', () => {
    state.name = clientName.value;
    nameError.textContent = '';
    nameGroup.classList.remove('has-error');
  });

  clientPhone.addEventListener('input', (e) => {
    let v = e.target.value.replace(/\D/g, '');
    if (v.length > 11) v = v.slice(0, 11);
    if (v.length > 6) {
      e.target.value = `(${v.slice(0,2)}) ${v.slice(2,7)}-${v.slice(7)}`;
    } else if (v.length > 2) {
      e.target.value = `(${v.slice(0,2)}) ${v.slice(2)}`;
    } else if (v.length > 0) {
      e.target.value = `(${v.slice(0,2)}`;
    } else {
      e.target.value = '';
    }
    state.phone = e.target.value;
    phoneError.textContent = '';
    phoneGroup.classList.remove('has-error');
  });

  clientNote.addEventListener('input', () => {
    state.note = clientNote.value;
  });

  myBookingsBtn.addEventListener('click', openModal);
  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay.classList.contains('open')) {
      closeModal();
    }
  });
}

function handleNext() {
  if (!validateStep(state.step)) return;
  if (state.step === 2) {
    dateDisplay.textContent = formatDateLong(state.selectedDate);
    renderTimeSlots();
  }
  if (state.step < 5) {
    state.step++;
    updateUI();
  }
}

function handleBack() {
  if (state.step > 1 && state.step < 5) {
    state.step--;
    updateUI();
  }
}

function validateStep(step) {
  let valid = true;

  if (step === 1) {
    if (!state.selectedService) {
      showToast('Selecione um serviço para continuar.');
      valid = false;
    }
  }

  if (step === 2) {
    if (!dateInput.value) {
      dateError.textContent = 'Escolha uma data.';
      dateField.classList.add('has-error');
      valid = false;
    } else {
      state.selectedDate = dateInput.value;
    }
  }

  if (step === 3) {
    if (!state.selectedTime) {
      timeError.textContent = 'Escolha um horário disponível.';
      valid = false;
    }
  }

  if (step === 4) {
    const nameVal = clientName.value.trim();
    if (!nameVal) {
      nameError.textContent = 'Informe seu nome.';
      nameGroup.classList.add('has-error');
      valid = false;
    } else {
      state.name = nameVal;
      nameGroup.classList.remove('has-error');
    }

    const phoneDigits = clientPhone.value.replace(/\D/g, '');
    if (phoneDigits.length < 10) {
      phoneError.textContent = 'Informe um WhatsApp válido com DDD.';
      phoneGroup.classList.add('has-error');
      valid = false;
    } else {
      state.phone = clientPhone.value.trim();
      phoneGroup.classList.remove('has-error');
    }

    if (valid) {
      confirmBooking();
      return false;
    }
  }

  return valid;
}

function showToast(message) {
  let toast = document.getElementById('step-error-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'step-error-toast';
    toast.className = 'step-toast';
    document.querySelector('.main-panel').prepend(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toast.classList.remove('show'), 3200);
}

function clearErrors() {
  dateError.textContent = '';
  timeError.textContent = '';
  nameError.textContent = '';
  phoneError.textContent = '';
  nameGroup.classList.remove('has-error');
  phoneGroup.classList.remove('has-error');
  dateField.classList.remove('has-error');
  const toast = document.getElementById('step-error-toast');
  if (toast) toast.classList.remove('show');
}

function updateUI() {
  stepPanels.forEach((panel, idx) => {
    panel.classList.toggle('active', idx + 1 === state.step);
  });

  stepperSteps.forEach((step, idx) => {
    const num = idx + 1;
    step.classList.remove('active', 'done');
    if (num === state.step) step.classList.add('active');
    else if (num < state.step) step.classList.add('done');
  });

  stepperLines.forEach((line, idx) => {
    line.classList.toggle('filled', idx + 1 < state.step);
  });

  searchWrap.style.display = state.step === 1 ? 'block' : 'none';

  if (state.step === 5) {
    backBtn.style.visibility = 'hidden';
    nextBtn.style.display = 'none';
  } else {
    backBtn.style.visibility = state.step === 1 ? 'hidden' : 'visible';
    nextBtn.style.display = 'inline-flex';
    nextBtn.textContent = state.step === 4 ? 'Confirmar agendamento' : 'Avançar';
  }
}

function confirmBooking() {
  const bookings = getBookings();
  const exists = bookings.some(b => b.date === state.selectedDate && b.time === state.selectedTime);
  if (exists) {
    timeError.textContent = 'Este horário já foi reservado. Escolha outro.';
    state.step = 3;
    updateUI();
    renderTimeSlots();
    return;
  }

  const booking = {
    service: state.selectedService.name,
    date: state.selectedDate,
    time: state.selectedTime,
    price: state.selectedService.price,
    name: state.name,
    phone: state.phone,
    note: state.note,
    createdAt: new Date().toISOString()
  };

  bookings.push(booking);
  localStorage.setItem('agenda_bookings', JSON.stringify(bookings));

  receiptService.textContent = booking.service;
  receiptDate.textContent = formatDateLong(booking.date);
  receiptTime.textContent = booking.time;
  receiptPrice.textContent = formatCurrency(booking.price);

  const msg = `Olá! Me chamo ${booking.name} e acabei de solicitar um agendamento.\n\nServiço: ${booking.service}\nData: ${formatDateLong(booking.date)}\nHorário: ${booking.time}\n\nPoderia confirmar?`;
  whatsappBtn.href = `https://wa.me/${business.phone}?text=${encodeURIComponent(msg)}`;

  state.step = 5;
  updateUI();
}

function getBookings() {
  try {
    return JSON.parse(localStorage.getItem('agenda_bookings')) || [];
  } catch {
    return [];
  }
}

function openModal() {
  const bookings = getBookings();
  if (bookings.length === 0) {
    modalBody.innerHTML = `<p class="modal-empty">Nenhum agendamento encontrado.</p>`;
  } else {
    modalBody.innerHTML = bookings.slice().reverse().map(b => `
      <div class="booking-item">
        <strong>${b.service}</strong>
        <p>${formatDateLong(b.date)} às ${b.time} — ${formatCurrency(b.price)}</p>
      </div>
    `).join('');
  }
  modalOverlay.classList.add('open');
  modalOverlay.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modalOverlay.classList.remove('open');
  modalOverlay.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

function formatDateLong(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
}

init();
