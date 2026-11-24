(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.documentElement.classList.add("game-ui-ready");

  function animateCounter(counter) {
    const end = Number(counter.dataset.countUp);
    const start = Number(counter.dataset.countStart ?? end);
    if (reducedMotion || !Number.isFinite(start) || !Number.isFinite(end) || start === end) return;

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
  }

  function initializeCounters(root = document) {
    root.querySelectorAll("[data-count-up]").forEach(animateCounter);
  }

  function mapState(value) {
    if (value < 50) return ["attention", "需要關注"];
    if (value < 75) return ["steady", "穩定推進"];
    return ["strong", "進展良好"];
  }

  function updateCampusMap(animateChanges = false) {
    const metricCards = Array.from(document.querySelectorAll(".metric-card[data-metric]"));
    document.querySelectorAll(".map-zone[data-map-metric]").forEach((zone) => {
      const metric = metricCards.find((card) => card.dataset.metric === zone.dataset.mapMetric);
      const value = Number(metric?.dataset.value);
      if (!Number.isFinite(value)) return;

      const previousValue = zone.dataset.currentValue;
      const changed = previousValue !== undefined && Number(previousValue) !== value;
      const [state, status] = mapState(value);
      zone.dataset.currentValue = String(value);
      zone.dataset.mapState = state;
      zone.querySelector("[data-map-value]").textContent = String(value);
      zone.querySelector("[data-map-status]").textContent = status;

      if (changed && animateChanges && !reducedMotion) {
        zone.classList.remove("is-updated");
        void zone.getBoundingClientRect();
        zone.classList.add("is-updated");
        window.setTimeout(() => zone.classList.remove("is-updated"), 420);
      }
    });

  }

  function updateRoundView(update) {
    const screen = document.querySelector(".simulation-screen");
    const roundNumber = Number(update.dataset.roundNumber);
    const roundCount = Number(update.dataset.roundCount);
    if (!screen || !Number.isInteger(roundNumber) || !Number.isInteger(roundCount)) {
      throw new Error("Missing simulation view state");
    }

    const selectors = ["#resource-panel", ".event-panel", ".decision-panel"];
    const panels = selectors.map((selector) => ({
      current: screen.querySelector(selector),
      incoming: update.querySelector(selector),
    }));
    if (panels.some(({ current, incoming }) => !current || !incoming)) {
      throw new Error("Incomplete simulation update");
    }

    panels.forEach(({ current, incoming }) => {
      current.replaceWith(document.importNode(incoming, true));
    });
    screen.dataset.roundNumber = String(roundNumber);
    screen.dataset.roundCount = String(roundCount);

    const roundCounter = screen.querySelector(".round-counter strong");
    const progress = screen.querySelector(".hud-progress");
    if (roundCounter) roundCounter.textContent = `回合 ${roundNumber} / ${roundCount}`;
    if (progress) {
      progress.setAttribute("aria-valuenow", String(roundNumber));
      progress.style.setProperty("--progress", `${(roundNumber * 100) / roundCount}%`);
    }

    const eventPanel = screen.querySelector(".event-panel");
    initializeCounters(screen);
    updateCampusMap(true);
    eventPanel.querySelector("h2")?.focus({ preventScroll: true });
  }

  function updateFinalView(screen, resultDocument, resultUrl) {
    const resultMetrics = Array.from(resultDocument.querySelectorAll(".result-page [data-metric]"));
    const currentMetrics = Array.from(screen.querySelectorAll(".metric-card[data-metric]"));
    if (resultMetrics.length !== currentMetrics.length) {
      throw new Error("Final metric data is incomplete");
    }

    resultMetrics.forEach((resultMetric) => {
      const current = currentMetrics.find((metric) => metric.dataset.metric === resultMetric.dataset.metric);
      if (!current) throw new Error("Final metric does not match the simulation");

      const previousValue = Number(current.dataset.value);
      const value = Number(resultMetric.dataset.value);
      const change = value - previousValue;
      current.dataset.value = String(value);

      const counter = current.querySelector(".metric-value");
      counter.dataset.countStart = String(previousValue);
      counter.dataset.countUp = String(value);
      counter.textContent = String(value);
      animateCounter(counter);

      const changeLabel = current.querySelector(".metric-change");
      changeLabel.classList.remove("is-positive", "is-negative", "is-neutral");
      changeLabel.classList.add(change > 0 ? "is-positive" : change < 0 ? "is-negative" : "is-neutral");
      changeLabel.textContent = change > 0 ? `+${change} 本回合` : change < 0 ? `${change} 本回合` : "本回合無變化";
    });

    const roundCount = Number(screen.dataset.roundCount);
    const progress = screen.querySelector(".hud-progress");
    if (progress) {
      progress.setAttribute("aria-valuenow", String(roundCount));
      progress.style.setProperty("--progress", "100%");
    }
    const completedCount = screen.querySelector(".decision-panel .board-heading > span");
    if (completedCount) completedCount.textContent = `${roundCount} / ${roundCount} 已完成`;

    const currentDecision = screen.querySelector(".decision-timeline .is-current");
    const lastAction = resultDocument.querySelector(".action-list li:last-child");
    if (currentDecision && lastAction) {
      currentDecision.classList.remove("is-current");
      currentDecision.classList.add("is-complete");
      currentDecision.removeAttribute("aria-current");
      currentDecision.querySelector(".timeline-marker").textContent = "✓";
      currentDecision.querySelector("small").textContent = `回合 ${roundCount}`;
      currentDecision.querySelector("strong").textContent =
        lastAction.querySelector("span")?.textContent.trim() || "已完成決策";
    }

    const form = screen.querySelector(".event-panel form");
    if (form) form.hidden = true;
    const processing = screen.querySelector(".round-processing");
    if (processing) {
      processing.textContent = "本回合政策已執行，校園地圖與指標已更新。";
      processing.hidden = false;
    }
    updateCampusMap(true);

    const resultNodes = Array.from(resultDocument.body.childNodes)
      .filter((node) => node.nodeName.toLowerCase() !== "script")
      .map((node) => document.importNode(node, true));
    const delay = reducedMotion ? 0 : 520;
    window.setTimeout(() => {
      document.title = resultDocument.title;
      document.body.className = resultDocument.body.className;
      document.body.replaceChildren(...resultNodes);
      window.history.pushState({ campusResult: true }, "", resultUrl);
      initializeCounters();
    }, delay);
  }

  async function submitRound(form) {
    const submit = form.querySelector('button[type="submit"]');
    const feedback = form.querySelector(".game-feedback");
    const processing = form.closest(".event-panel")?.querySelector(".round-processing");
    form.dataset.submitting = "true";
    form.classList.add("is-submitting");
    if (submit) {
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
    }
    if (feedback) feedback.hidden = true;
    if (processing) {
      processing.textContent = "正在套用政策並更新校園狀態…";
      processing.hidden = false;
    }

    try {
      const response = await window.fetch(form.action, {
        method: form.method.toUpperCase(),
        body: new FormData(form),
        headers: { "X-Game-Update": "1" },
      });
      if (!response.ok) throw new Error(`Simulation update failed (${response.status})`);
      const html = await response.text();
      const parsed = new DOMParser().parseFromString(html, "text/html");
      const update = parsed.querySelector("[data-game-update]");
      if (update) {
        updateRoundView(update);
      } else if (parsed.querySelector(".result-page")) {
        updateFinalView(document.querySelector(".simulation-screen"), parsed, response.url);
      } else {
        throw new Error("Simulation update fragment was not returned");
      }
    } catch (error) {
      console.error("Could not update the simulation round.", error);
      if (form.isConnected) {
        form.dataset.submitting = "false";
        form.classList.remove("is-submitting");
        if (submit) {
          submit.disabled = false;
          submit.removeAttribute("aria-busy");
        }
        if (processing) processing.hidden = true;
        if (feedback) {
          feedback.textContent = "本回合更新失敗，請確認連線後重試。";
          feedback.hidden = false;
        }
      }
    }
  }

  document.addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || input.type !== "radio") return;
    const form = input.closest("form[data-game-submit]");
    if (!form) return;
    form.querySelectorAll('input[type="radio"]').forEach((option) => {
      option.closest(".option")?.classList.toggle("is-selected", option.checked);
    });
  });

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.matches("form[data-game-submit]")) return;
    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }

    const screen = form.closest(".simulation-screen");
    if (form.hasAttribute("data-simulation-form") && screen && window.fetch) {
      event.preventDefault();
      submitRound(form);
      return;
    }

    if (reducedMotion) return;
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

  initializeCounters();
  updateCampusMap();
})();
