// Quick Exit: shows custom confirmation modal, then leaves and removes this page from history.
function quickExit() {
  const overlay = document.getElementById("qe-overlay");
  const btnLeave = document.getElementById("qe-leave");
  const btnStay = document.getElementById("qe-stay");

  overlay.classList.add("is-open");
  btnLeave.focus();

  function close() {
    overlay.classList.remove("is-open");
    btnLeave.removeEventListener("click", leave);
    btnStay.removeEventListener("click", close);
    document.removeEventListener("keydown", onKey);
  }

  function leave() {
    close();
    window.location.replace("https://www.google.com");
  }

  function onKey(e) {
    if (e.key === "Escape") close();
    if (e.key === "Enter" && document.activeElement === btnLeave) leave();
  }

  btnLeave.addEventListener("click", leave);
  btnStay.addEventListener("click", close);
  document.addEventListener("keydown", onKey);
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

// Theme switcher — dark / light / system
function getTheme() {
  return localStorage.getItem("theme") || "system";
}

function resolveTheme(mode) {
  if (mode === "dark" || mode === "light") return mode;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function setTheme(mode) {
  localStorage.setItem("theme", mode);
  document.documentElement.setAttribute("data-theme", resolveTheme(mode));
  syncSwitcherUI(mode);
}

function syncSwitcherUI(mode) {
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    const isActive = btn.getAttribute("data-theme-toggle") === mode;
    btn.setAttribute("aria-checked", isActive ? "true" : "false");
  });
}

document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
  btn.addEventListener("click", () => {
    setTheme(btn.getAttribute("data-theme-toggle"));
  });
});

// Sync UI on load
syncSwitcherUI(getTheme());

// Listen for OS preference changes (only if user is in system mode)
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (getTheme() === "system") {
    document.documentElement.setAttribute("data-theme", resolveTheme("system"));
  }
});

// Form submit loading feedback — disables button and shows spinner
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn && !btn.classList.contains("btn--loading")) {
      btn.classList.add("btn--loading");
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
    }
  });
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