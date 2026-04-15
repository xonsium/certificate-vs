(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const eventTemplates = Array.from(document.querySelectorAll("[data-event-template]"));

  const step2 = document.getElementById("step-2");
  const step3 = document.getElementById("step-3");
  const step4 = document.getElementById("step-4");
  const selectedLabel = document.getElementById("selected-event-label");
  const codeInput = document.getElementById("code-input");
  const verifyBtn = document.getElementById("verify-btn");
  const verifyLabel = document.getElementById("verify-label");
  const verifySpinner = document.getElementById("verify-spinner");
  const verifyError = document.getElementById("verify-error");
  const downloadPdfBtn = document.getElementById("download-pdf-btn");

  let selectedEvent = null;
  let lastPayload = null;
  let activeTemplate = eventTemplates.find((x) => x.classList.contains("active")) || null;

  function show(el) {
    el.classList.remove("hidden");
    el.classList.add("step-enter");
  }

  function hide(el) {
    el.classList.add("hidden");
    el.classList.remove("step-enter");
  }

  function setLoading(loading) {
    verifyBtn.disabled = loading;
    verifyLabel.classList.toggle("hidden", loading);
    verifySpinner.classList.toggle("hidden", !loading);
  }

  function setActiveTemplate(eventName) {
    activeTemplate = null;
    eventTemplates.forEach((tpl) => {
      const isActive = tpl.dataset.eventTemplate === eventName;
      tpl.classList.toggle("active", isActive);
      tpl.classList.toggle("print-active", isActive);
      if (isActive) activeTemplate = tpl;
    });
  }

  function fillTemplate(p) {
    if (!activeTemplate) return;
    const fields = {
      name: p.name,
      institution: p.institution,
      segment: p.segment,
      prize_place: p.prize_place,
      installment: p.installment,
      code_label: "Code: " + p.code,
    };
    Object.entries(fields).forEach(([key, value]) => {
      activeTemplate.querySelectorAll(`[data-cert-field="${key}"]`).forEach((el) => {
        el.textContent = value || "";
      });
    });
  }

  function copyComputedStyles(source, target) {
    const computed = window.getComputedStyle(source);
    [
      "color",
      "backgroundColor",
      "backgroundImage",
      "borderColor",
      "borderTopColor",
      "borderRightColor",
      "borderBottomColor",
      "borderLeftColor",
      "boxShadow",
      "textShadow",
      "filter",
    ].forEach((prop) => {
      if (computed[prop]) {
        let value = computed[prop];
        // Convert oklch to rgb if needed
        if (value.includes("oklch")) {
          const rgbMatch = window.getComputedStyle(source, null).getPropertyValue(prop);
          if (rgbMatch && rgbMatch.includes("rgb")) {
            value = rgbMatch;
          }
        }
        target.style[prop] = value;
      }
    });
  }

  document.querySelectorAll("[data-event]").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedEvent = btn.dataset.event || null;
      selectedLabel.textContent = selectedEvent || "";
      setActiveTemplate(selectedEvent);
      codeInput.value = "";
      verifyError.classList.add("hidden");
      hide(step3);
      hide(step4);
      show(step2);
      codeInput.focus();
    });
  });

  codeInput?.addEventListener("input", () => {
    codeInput.value = codeInput.value.replace(/[^a-zA-Z0-9]/g, "").slice(0, 6).toUpperCase();
  });

  async function verify() {
    if (!selectedEvent) return;
    const code = (codeInput.value || "").trim().toUpperCase();
    if (!/^[A-Za-z0-9]{6}$/.test(code)) {
      verifyError.textContent = "Please enter a valid 6-character code.";
      verifyError.classList.remove("hidden");
      return;
    }
    verifyError.classList.add("hidden");
    setLoading(true);
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({ event: selectedEvent, code }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        verifyError.textContent =
          data.error === "not_found"
            ? "Invalid code or event combination."
            : "Something went wrong. Please try again.";
        verifyError.classList.remove("hidden");
        hide(step3);
        hide(step4);
        return;
      }
      const c = data.certificate;
      lastPayload = { event: selectedEvent, code, ...c };
      document.getElementById("res-name").textContent = c.name;
      document.getElementById("res-institution").textContent = c.institution;
      document.getElementById("res-segment").textContent = c.segment;
      document.getElementById("res-prize").textContent = c.prize_place;
      document.getElementById("res-installment").textContent = c.installment;

      fillTemplate(lastPayload);
      show(step3);
      show(step4);
      step3.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch {
      verifyError.textContent = "Network error. Please try again.";
      verifyError.classList.remove("hidden");
    } finally {
      setLoading(false);
    }
  }

  function getActiveTemplate() {
    // First check if activeTemplate is still valid and has the active class
    if (activeTemplate && activeTemplate.classList.contains("active")) {
      return activeTemplate;
    }
    // Otherwise find the active template by class
    const found = eventTemplates.find((x) => x.classList.contains("active"));
    if (found) {
      activeTemplate = found;
      return found;
    }
    // Fallback to activeTemplate if it exists
    return activeTemplate;
  }

  async function downloadPdf() {
    const captureEl = getActiveTemplate();
    if (!captureEl || !lastPayload || typeof html2canvas === "undefined") return;
    const { jsPDF } = window.jspdf || {};
    if (!jsPDF) return;

    const originalText = downloadPdfBtn?.textContent || "";
    if (downloadPdfBtn) {
      downloadPdfBtn.disabled = true;
      downloadPdfBtn.textContent = "Generating PDF...";
    }

    try {
      const canvas = await html2canvas(captureEl, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
        windowWidth: captureEl.scrollWidth,
        windowHeight: captureEl.scrollHeight,
        onclone: (clonedDoc) => {
          const cloneRoot = clonedDoc.querySelector(
            `[data-event-template="${lastPayload.event}"]`
          );
          if (!cloneRoot) return;
          copyComputedStyles(captureEl, cloneRoot);
          const originals = Array.from(captureEl.querySelectorAll("*"));
          const clones = Array.from(cloneRoot.querySelectorAll("*"));
          originals.forEach((orig, index) => {
            const clone = clones[index];
            if (!clone) return;
            copyComputedStyles(orig, clone);
          });
        },
      });
      const img = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "landscape",
        unit: "px",
        format: [canvas.width, canvas.height],
      });
      pdf.addImage(img, "PNG", 0, 0, canvas.width, canvas.height);
      const safeName =
        (lastPayload.name || "certificate").replace(/[^\w\s-]/g, "").trim().slice(0, 40) ||
        "certificate";
      pdf.save(`${safeName}-${lastPayload.event}-certificate.pdf`);
    } catch (err) {
      console.error(err);
      verifyError.textContent = "Unable to generate PDF. Please try again.";
      verifyError.classList.remove("hidden");
    } finally {
      if (downloadPdfBtn) {
        downloadPdfBtn.disabled = false;
        downloadPdfBtn.textContent = originalText;
      }
    }
  }

  verifyBtn?.addEventListener("click", verify);
  codeInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") verify();
  });
  document.getElementById("download-pdf-btn")?.addEventListener("click", downloadPdf);
  document.getElementById("print-btn")?.addEventListener("click", () => window.print());
})();
