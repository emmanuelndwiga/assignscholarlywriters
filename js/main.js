document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar');
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  hamburger?.addEventListener('click', () => {
    mobileMenu.classList.toggle('active');
  });

  document.querySelectorAll('.mobile-menu a').forEach(link => {
    link.addEventListener('click', () => {
      mobileMenu.classList.remove('active');
    });
  });

  const navFaq = document.querySelector('.nav-faq');
  const faqToggle = document.querySelector('.nav-faq-toggle');
  if (faqToggle && navFaq) {
    faqToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      navFaq.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
      if (!navFaq.contains(e.target)) {
        navFaq.classList.remove('open');
      }
    });
  }

  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, observerOptions);

  document.querySelectorAll('.feature-card, .service-card, .pricing-card, .review-card, .sample-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
  });
});
