// Quick Exit: leaves immediately and removes this page from history.
function quickExit() {
  window.location.replace("https://www.google.com");
}

document.querySelectorAll("[data-quick-exit]").forEach((btn) => {
  btn.addEventListener("click", quickExit);
});

// Triple-tap Escape as a panic-key fallback (won't fire on a single stray press)
let escPresses = 0;
let escTimer = null;
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  escPresses += 1;
  clearTimeout(escTimer);
  if (escPresses >= 3) {
    quickExit();
    return;
  }
  escTimer = setTimeout(() => { escPresses = 0; }, 1200);
});

// Scroll-reveal, reduced-motion aware
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!prefersReducedMotion && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
} else {
  document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
}