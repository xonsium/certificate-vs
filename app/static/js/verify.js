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

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        verifyError.textContent =
          data.error === "not_found"
            ? "Certificate not found. Please verify again."
            : "Unable to generate PDF. Please try again.";
        verifyError.classList.remove("hidden");
        return;
      }

      // Create a temporary container to render the HTML
      const container = document.createElement("div");
      container.innerHTML = data.html;
      container.style.position = "absolute";
      container.style.left = "-9999px";
      container.style.top = "0";
      container.style.width = "1200px";
      container.style.height = "850px";
      container.style.background = "white";
      document.body.appendChild(container);

      // Use html2canvas to capture the certificate
      if (typeof html2canvas === "undefined") {
        // Load html2canvas dynamically
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
        document.head.appendChild(script);
        await new Promise((resolve) => {
          script.onload = resolve;
          script.onerror = resolve;
        });
      }

      const canvas = await html2canvas(container, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      // Convert canvas to PDF using jsPDF
      if (typeof jspdf === "undefined") {
        const pdfScript = document.createElement("script");
        pdfScript.src = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";
        document.head.appendChild(pdfScript);
        await new Promise((resolve) => {
          pdfScript.onload = resolve;
          pdfScript.onerror = resolve;
        });
      }

      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF({
        orientation: "landscape",
        unit: "px",
        format: [canvas.width / 2, canvas.height / 2],
      });

      pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, canvas.width / 2, canvas.height / 2);
      pdf.save(`${data.filename}.pdf`);

      // Clean up
      document.body.removeChild(container);
      verifyError.classList.add("hidden");
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
})();
