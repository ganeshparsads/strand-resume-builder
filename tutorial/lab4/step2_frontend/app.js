/**
 * Step 2: Frontend JavaScript
 *
 * Handles:
 * - PDF file upload (drag & drop + click)
 * - Base64 encoding of PDF
 * - API calls to /invocations
 * - Response parsing (extracts HTML from markdown code blocks)
 * - Version history tracking (client-side)
 * - Refinement flow
 */

const AGENT_ENDPOINT = ""; // Same origin (proxied by serve.py)
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

// --- File Upload ---
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
  updateBtn();
});

// Drag and drop
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && file.type === "application/pdf") {
    selectedFile = file;
    fileInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileInfo.hidden = false;
    updateBtn();
  } else {
    showStatus("Please upload a PDF file.", "error");
  }
});

jobDescription.addEventListener("input", updateBtn);

function updateBtn() {
  generateBtn.disabled = !(selectedFile && jobDescription.value.trim().length >= 50);
}

// --- Generate Resume ---
generateBtn.addEventListener("click", async () => {
  if (!selectedFile || !jobDescription.value.trim()) return;
  generateBtn.disabled = true;
  showStatus("Reading PDF and generating resume... This takes 3-5 minutes.", "loading");

  try {
    const pdfBase64 = await readFileAsBase64(selectedFile);
    const resp = await fetch(`${AGENT_ENDPOINT}/invocations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt:
          `Extract text from the PDF, parse resume and job description, ` +
          `match skills, generate ATS-friendly HTML resume, save version.\n\n` +
          `Job Description:\n${jobDescription.value.trim()}\n\n` +
          `Resume PDF base64:\n${pdfBase64}`,
      }),
    });
    const data = await resp.json();
    if (data.error) { showStatus(`Error: ${data.error}`, "error"); return; }
    renderResponse(data.result || "");
    showStatus("Resume generated!", "success");
    feedbackSection.hidden = false;
    downloadBtn.hidden = false;
    versionSidebar.hidden = false;
    addVersion("Initial generation");
  } catch (err) {
    showStatus(`Failed: ${err.message}`, "error");
  } finally {
    generateBtn.disabled = false;
    updateBtn();
  }
});

// --- Refine ---
refineBtn.addEventListener("click", async () => {
  const text = feedback.value.trim();
  if (!text) return;
  refineBtn.disabled = true;
  showStatus("Applying feedback...", "loading");
  try {
    const resp = await fetch(`${AGENT_ENDPOINT}/invocations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text }),
    });
    const data = await resp.json();
    if (data.error) { showStatus(`Error: ${data.error}`, "error"); return; }
    renderResponse(data.result || "");
    showStatus("Resume refined!", "success");
    addVersion(text);
    feedback.value = "";
  } catch (err) {
    showStatus(`Failed: ${err.message}`, "error");
  } finally {
    refineBtn.disabled = false;
  }
});

// --- Download ---
downloadBtn.addEventListener("click", () => {
  const w = window.open("", "_blank");
  w.document.write(preview.innerHTML);
  w.document.close();
  w.print();
});

// --- Helpers ---
function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderResponse(text) {
  const match = text.match(/```html\s*([\s\S]*?)```/);
  if (match) { preview.innerHTML = match[1]; }
  else if (text.includes("<html") || text.includes("<section")) { preview.innerHTML = text; }
  else { preview.innerHTML = `<pre style="white-space:pre-wrap">${text}</pre>`; }
}

function showStatus(msg, type) {
  status.textContent = msg;
  status.className = `status ${type}`;
  status.hidden = false;
  if (type === "success") setTimeout(() => (status.hidden = true), 5000);
}

function addVersion(label) {
  versions.push({ label, time: new Date().toLocaleTimeString(), html: preview.innerHTML });
  versionList.innerHTML = versions.map((v, i) =>
    `<li><button class="version-btn" data-i="${i}">v${i+1} - ${v.time}<br><small>${v.label.slice(0,40)}</small></button></li>`
  ).reverse().join("");
  versionList.querySelectorAll(".version-btn").forEach(b =>
    b.addEventListener("click", () => { preview.innerHTML = versions[b.dataset.i].html; })
  );
}
