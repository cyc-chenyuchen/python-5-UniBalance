(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.documentElement.classList.add("game-ui-ready");

  if (!reducedMotion) {
    document.querySelectorAll("[data-count-up]").forEach((counter) => {
      const end = Number(counter.dataset.countUp);
      const start = Number(counter.dataset.countStart ?? end);

      if (!Number.isFinite(start) || !Number.isFinite(end) || start === end) return;

      const duration = 480;
      let startTime;
      counter.textContent = String(Math.round(start));

      const tick = (timestamp) => {
        startTime ??= timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const eased = 1 - (1 - progress) ** 3;
        counter.textContent = String(Math.round(start + (end - start) * eased));
        if (progress < 1) window.requestAnimationFrame(tick);
      };

      window.requestAnimationFrame(tick);
    });
  }

  document.querySelectorAll("form[data-game-submit]").forEach((form) => {
    const options = form.querySelectorAll('input[type="radio"]');
    options.forEach((input) => {
      input.addEventListener("change", () => {
        options.forEach((option) => {
          option.closest(".option")?.classList.toggle("is-selected", option.checked);
        });
      });
    });

    form.addEventListener("submit", (event) => {
      if (reducedMotion || form.dataset.submitting === "true") return;
      event.preventDefault();
      form.dataset.submitting = "true";
      form.classList.add("is-submitting");
      const submit = form.querySelector('button[type="submit"]');
      if (submit) {
        submit.disabled = true;
        submit.setAttribute("aria-busy", "true");
      }
      window.setTimeout(() => form.submit(), 180);
    });
  });
})();
