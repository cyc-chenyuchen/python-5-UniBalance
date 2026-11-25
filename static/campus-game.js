(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const facilities = Array.from(document.querySelectorAll(".map-facility[data-facility-id]"));
  const inspector = document.querySelector("#map-inspector");

  function showFacility(facility) {
    if (!inspector) return;

    facilities.forEach((item) => {
      const selected = item === facility;
      item.classList.toggle("is-selected", selected);
      item.setAttribute("aria-pressed", String(selected));
    });

    const values = {
      "[data-map-info-name]": facility.dataset.facilityName,
      "[data-map-info-level]": `LV. ${facility.dataset.facilityLevel} / 3`,
      "[data-map-info-status]": facility.dataset.facilityStatus,
      "[data-map-info-description]": facility.dataset.facilityDescription,
      "[data-map-info-next]": facility.dataset.facilityNext,
      "[data-map-info-completed]": facility.dataset.facilityCompleted,
      "[data-map-info-policies]": facility.dataset.facilityPolicies,
      "[data-map-info-issue]": facility.dataset.facilityIssue,
    };

    Object.entries(values).forEach(([selector, value]) => {
      const element = inspector.querySelector(selector);
      if (element) element.textContent = value || "目前沒有資料。";
    });
  }

  facilities.forEach((facility) => {
    facility.addEventListener("click", () => showFacility(facility));
    facility.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      showFacility(facility);
    });
  });

  function selectCard(input) {
    const form = input.closest("form");
    if (!form) return;
    form.querySelectorAll('input[type="radio"]').forEach((radio) => {
      const card = radio.closest(".campaign-option");
      if (card) card.classList.toggle("is-selected", radio.checked);
    });
  }

  document.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement) || event.target.type !== "radio") return;
    selectCard(event.target);
  });

  document.querySelectorAll('.campaign-option input[type="radio"]:checked').forEach(selectCard);

  function getSnapshot() {
    const campaign = document.querySelector(".campaign-play");
    if (!campaign) return null;

    const values = {};
    document.querySelectorAll(".map-facility[data-facility-id]").forEach((facility) => {
      values[`building:${facility.dataset.facilityId}`] = Number(facility.dataset.facilityLevel);
    });
    document.querySelectorAll(".map-resource-node[data-resource-value]").forEach((resource) => {
      const key = Array.from(resource.classList).find((name) => name.startsWith("map-") && name !== "map-resource-node");
      if (key) values[key] = Number(resource.dataset.resourceValue);
    });
    document.querySelectorAll(".metric-orb-card[data-metric]").forEach((metric) => {
      values[`metric:${metric.dataset.metric}`] = Number(metric.dataset.value);
    });
    const treasury = document.querySelector("[data-treasury-value]");
    if (treasury) values.treasury = Number(treasury.dataset.treasuryValue);

    return {
      campaignTurn: campaign.dataset.campaignTurn,
      values,
    };
  }

  function animateCounter(element, start, end, onUpdate) {
    if (!element || reducedMotion || start === end) return;
    let startTime;
    const duration = 520;

    const tick = (timestamp) => {
      startTime ??= timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - (1 - progress) ** 3;
      const value = Math.round(start + (end - start) * eased);
      element.textContent = String(value);
      if (onUpdate) onUpdate(value);
      if (progress < 1) window.requestAnimationFrame(tick);
    };
    window.requestAnimationFrame(tick);
  }

  function animateCampaignUpdate() {
    const current = getSnapshot();
    if (!current) return;

    const snapshotKey = "unibalance-campus-display-state";
    let previous = null;
    try {
      previous = JSON.parse(window.sessionStorage.getItem(snapshotKey) || "null");
    } catch (error) {
      console.warn("Could not read the previous campus display state.", error);
    }

    const advancedOneTurn = previous
      && Number(current.campaignTurn) === Number(previous.campaignTurn) + 1;
    if (advancedOneTurn && previous.values) {
      const changed = new Set(
        Object.keys(current.values).filter((key) => previous.values[key] !== current.values[key]),
      );
      if (!reducedMotion && changed.size) {
        facilities.forEach((facility) => {
          if (!changed.has(`building:${facility.dataset.facilityId}`)) return;
          facility.classList.add("is-updated");
          window.setTimeout(() => facility.classList.remove("is-updated"), 850);
        });
        document.querySelectorAll(".metric-orb-card[data-metric]").forEach((metric) => {
          const key = `metric:${metric.dataset.metric}`;
          if (!changed.has(key)) return;
          metric.classList.add("is-updated");
          const number = metric.querySelector(".metric-orb span");
          const gauge = metric.querySelector(".metric-orb");
          animateCounter(number, previous.values[key], current.values[key], (value) => {
            if (gauge) gauge.style.setProperty("--metric-value", value);
          });
          window.setTimeout(() => metric.classList.remove("is-updated"), 700);
        });
        document.querySelectorAll(".map-resource-card[data-resource-name]").forEach((card) => {
          const key = `map-${card.dataset.resourceName}`;
          if (!changed.has(key)) return;
          card.classList.add("is-updated");
          const number = card.querySelector(".resource-count");
          const meter = card.querySelector(".resource-meter");
          animateCounter(number, previous.values[key], current.values[key], (value) => {
            if (meter) meter.style.setProperty("--resource-value", `${value}%`);
          });
          window.setTimeout(() => card.classList.remove("is-updated"), 700);
        });
        document.querySelectorAll(".map-resource-node[data-resource-value]").forEach((resource) => {
          const name = Array.from(resource.classList).find((className) => className.startsWith("map-") && className !== "map-resource-node");
          if (!name || !changed.has(name)) return;
          const number = resource.querySelector(".map-resource-value");
          animateCounter(number, previous.values[name], current.values[name]);
        });
        if (changed.has("treasury")) {
          const budget = document.querySelector(".campaign-budget");
          const number = document.querySelector("[data-treasury-value]");
          if (budget) budget.classList.add("is-updated");
          animateCounter(number, previous.values.treasury, current.values.treasury);
          window.setTimeout(() => {
            if (budget) budget.classList.remove("is-updated");
          }, 700);
        }
      }
    }

    try {
      window.sessionStorage.setItem(snapshotKey, JSON.stringify(current));
    } catch (error) {
      console.warn("Could not save the campus display state for animations.", error);
    }
  }

  animateCampaignUpdate();
})();
