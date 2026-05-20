document.addEventListener('DOMContentLoaded', () => {
  // Header scroll effect
  const header = document.getElementById('header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  // Mobile menu
  const menuToggle = document.getElementById('menuToggle');
  const nav = document.getElementById('nav');
  menuToggle.addEventListener('click', () => {
    menuToggle.classList.toggle('active');
    nav.classList.toggle('open');
  });
  nav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menuToggle.classList.remove('active');
      nav.classList.remove('open');
    });
  });

  // Reveal on scroll
  const reveals = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  reveals.forEach(el => revealObserver.observe(el));

  // Booking widget logic
  const serviceChips = document.querySelectorAll('.service-chip');
  const timeChips = document.querySelectorAll('.time-chip');
  const dateInput = document.getElementById('bookingDate');
  const confirmBtn = document.getElementById('confirmBooking');

  let selectedService = null;
  let selectedDate = null;
  let selectedTime = null;

  // Set min date to today
  const today = new Date().toISOString().split('T')[0];
  dateInput.min = today;

  serviceChips.forEach(chip => {
    chip.addEventListener('click', () => {
      serviceChips.forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      selectedService = chip.dataset.service;
      updateSteps(2);
    });
  });

  dateInput.addEventListener('change', () => {
    if (dateInput.value) {
      selectedDate = dateInput.value;
      updateSteps(3);
    }
  });

  timeChips.forEach(chip => {
    chip.addEventListener('click', () => {
      timeChips.forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      selectedTime = chip.textContent.trim();
    });
  });

  function updateSteps(activeStep) {
    document.querySelectorAll('.booking-step').forEach(step => {
      const stepNum = parseInt(step.dataset.step);
      step.classList.remove('active', 'completed');
      if (stepNum === activeStep) {
        step.classList.add('active');
      } else if (stepNum < activeStep) {
        step.classList.add('completed');
      }
    });
  }

  confirmBtn.addEventListener('click', () => {
    if (!selectedService) {
      shakeWidget();
      highlightStep(1);
      return;
    }
    if (!selectedDate) {
      shakeWidget();
      highlightStep(2);
      return;
    }
    if (!selectedTime) {
      shakeWidget();
      highlightStep(3);
      return;
    }

    const msg = `Oi! Vi a Dress Hair Company e quero agendar um horário.\n\nServiço: ${selectedService}\nData: ${formatDate(selectedDate)}\nHorário: ${selectedTime}\n\nPode confirmar pra mim?`;
    const url = `https://wa.me/5521995280000?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');
  });

  function shakeWidget() {
    const widget = document.querySelector('.booking-widget');
    widget.style.animation = 'none';
    widget.offsetHeight; // reflow
    widget.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
      widget.style.animation = '';
    }, 500);
  }

  function highlightStep(stepNum) {
    const step = document.querySelector(`.booking-step[data-step="${stepNum}"]`);
    if (step) {
      step.style.transition = 'none';
      step.style.transform = 'translateX(-6px)';
      setTimeout(() => {
        step.style.transition = 'all 0.3s ease';
        step.style.transform = '';
      }, 100);
    }
  }

  function formatDate(dateStr) {
    const [y, m, d] = dateStr.split('-');
    return `${d}/${m}/${y}`;
  }
});

// Inject shake keyframe
const style = document.createElement('style');
style.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-8px); }
    40% { transform: translateX(8px); }
    60% { transform: translateX(-4px); }
    80% { transform: translateX(4px); }
  }
`;
document.head.appendChild(style);
