document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.feature-card, .service-card, .pricing-card, .review-card, .sample-card');

  if (!('IntersectionObserver' in window)) {
    // Fallback: show all cards immediately
    cards.forEach(card => {
      card.style.opacity = '1';
      card.style.transform = 'none';
    });
    return;
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

  cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
  });
});
