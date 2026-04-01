// Resume Modifier Agent - Frontend
const AGENT_ENDPOINT = "";

let sessionId = crypto.randomUUID();
let selectedFile = null;
let versions = [];

// DOM elements
const resumeUpload = document.getElementById("resume-upload");
const fileInfo = document.getElementById("file-info");
const jobDescription = document.getElementById("job-description");
const generateBtn = document.getElementById("generate-btn");
const refineBtn = document.getElementById("refine-btn");
const downloadBtn = document.getElementById("download-btn");
const preview = document.getElementById("preview");
const status = document.getElementById("status");
const feedbackSection = document.getElementById("feedback-section");
const feedback = document.getElementById("feedback");
const versionSidebar = document.getElementById("version-sidebar");
const versionList = document.getElementById("version-list");
const dropZone = document.getElementById("drop-zone");

// File upload handling
resumeUpload.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (file.type !== "application/pdf") {
    showStatus("Please upload a PDF file.", "error");
    e.target.value = "";
    return;
  }
  selectedFile = file;
  fileInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  fileInfo.hidden = false;
  updateGenerateButton();
});

// Drag and drop
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && file.type === "application/pdf") {
    selectedFile = file;
    fileInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileInfo.hidden = false;
    updateGenerateButton();
  } else {
    showStatus("Please upload a PDF file.", "error");
  }
});

// Job description input
jobDescription.addEventListener("input", updateGenerateButton);

function updateGenerateButton() {
  generateBtn.disabled = !(selectedFile && jobDescription.value.trim().length >= 50);
}

// Generate resume
generateBtn.addEventListener("click", async () => {
  if (!selectedFile || !jobDescription.value.trim()) return;

  showStatus("Reading PDF...", "loading");
  generateBtn.disabled = true;

  try {
    const pdfBase64 = await readFileAsBase64(selectedFile);
    showStatus("Extracting text and generating resume... This may take 30-60 seconds.", "loading");

    const response = await fetch(`${AGENT_ENDPOINT}/invocations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt:
          `Extract text from the PDF resume (base64 below), parse it, parse the job description, ` +
          `match skills, generate a tailored ATS-friendly HTML resume, and save the version.\n\n` +
          `Session ID: ${sessionId}\n` +
          `Job Description:\n${jobDescription.value.trim()}\n\n` +
          `Resume PDF base64:\n${pdfBase64}`,
      }),
    });

    const data = await response.json();
    if (data.error) {
      showStatus(`Error: ${data.error}`, "error");
      return;
    }

    renderResponse(data.result || data.response || "");
    showStatus("Resume generated successfully!", "success");
    feedbackSection.hidden = false;
    downloadBtn.hidden = false;
    versionSidebar.hidden = false;
    addVersion("Initial generation");
  } catch (err) {
    showStatus(`Failed to connect: ${err.message}`, "error");
  } finally {
    generateBtn.disabled = false;
    updateGenerateButton();
  }
});

// Refine resume
refineBtn.addEventListener("click", async () => {
  const feedbackText = feedback.value.trim();
  if (!feedbackText) return;

  showStatus("Applying feedback...", "loading");
  refineBtn.disabled = true;

  try {
    const response = await fetch(`${AGENT_ENDPOINT}/invocations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: feedbackText }),
    });

    const data = await response.json();
    if (data.error) {
      showStatus(`Error: ${data.error}`, "error");
      return;
    }

    renderResponse(data.result || data.response || "");
    showStatus("Resume refined!", "success");
    addVersion(feedbackText);
    feedback.value = "";
  } catch (err) {
    showStatus(`Failed: ${err.message}`, "error");
  } finally {
    refineBtn.disabled = false;
  }
});

// Download as PDF (browser print)
downloadBtn.addEventListener("click", () => {
  const printWindow = window.open("", "_blank");
  const htmlContent = preview.innerHTML;
  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.print();
});

// Helpers
function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderResponse(responseText) {
  // Try to extract HTML from the response (between ```html and ```)
  const htmlMatch = responseText.match(/```html\s*([\s\S]*?)```/);
  if (htmlMatch) {
    preview.innerHTML = htmlMatch[1];
  } else if (responseText.includes("<html") || responseText.includes("<section")) {
    preview.innerHTML = responseText;
  } else {
    preview.innerHTML = `<pre style="white-space:pre-wrap">${responseText}</pre>`;
  }
}

function showStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
  status.hidden = false;
  if (type === "success") {
    setTimeout(() => (status.hidden = true), 5000);
  }
}

function addVersion(label) {
  const now = new Date().toLocaleTimeString();
  versions.push({ label, time: now, html: preview.innerHTML });
  renderVersionList();
}

function renderVersionList() {
  versionList.innerHTML = versions
    .map(
      (v, i) =>
        `<li><button class="version-btn" data-index="${i}">` +
        `v${i + 1} - ${v.time}<br><small>${v.label.slice(0, 40)}</small></button></li>`
    )
    .reverse()
    .join("");

  versionList.querySelectorAll(".version-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.index);
      preview.innerHTML = versions[idx].html;
    });
  });
}
