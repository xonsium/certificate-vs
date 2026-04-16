(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";

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

  document.querySelectorAll("[data-event]").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedEvent = btn.dataset.event || null;
      selectedLabel.textContent = selectedEvent || "";
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
    if (!lastPayload) return;

    const originalText = downloadPdfBtn?.textContent || "";
    if (downloadPdfBtn) {
      downloadPdfBtn.disabled = true;
      downloadPdfBtn.textContent = "Generating PDF...";
    }

    try {
      const res = await fetch("/api/download-certificate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({
          event: lastPayload.event,
          code: lastPayload.code,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        verifyError.textContent =
          data.error === "not_found"
            ? "Certificate not found. Please verify again."
            : "Unable to generate PDF. Please try again.";
        verifyError.classList.remove("hidden");
        return;
      }

      // Get the PDF blob and trigger download
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName =
        (lastPayload.name || "certificate").replace(/[^\w\s-]/g, "").trim().toLowerCase().slice(0, 40) ||
        "certificate";
      a.download = `${safeName}-${lastPayload.event.toLowerCase()}-certificate.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      verifyError.classList.add("hidden");
    } catch (err) {
      console.error(err);
      verifyError.textContent = "Network error. Please try again.";
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
