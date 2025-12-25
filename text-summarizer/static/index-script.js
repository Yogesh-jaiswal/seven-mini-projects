/* ===============================
   DOM References
=============================== */
const summarizeBtn = document.querySelector(".primary-btn");
const copyBtn = document.querySelector(".copy");
const saveBtn = document.querySelector(".save");
const downloadBtn = document.querySelector(".download");
const textarea = document.querySelector("textarea");
const charCount = document.querySelector(".char-count");
const loader = document.querySelector(".skeleton-box");
const summaryCard = document.querySelector(".summary-card");


/* ===============================
   Toolbar State Control
=============================== */

/**
 * Enable or disable summary action tools.
 */
function toggleTools(state) {
  copyBtn.disabled = state;
  saveBtn.disabled = state;
  downloadBtn.disabled = state;
}

// Disable tools on initial load
toggleTools(true);


/* ===============================
   Summarization Flow
=============================== */

summarizeBtn.addEventListener("click", async () => {
  // Lock UI during request
  summarizeBtn.disabled = true;
  toggleTools(true);

  // Show loader, hide previous summary
  loader.classList.remove("hidden");
  summaryCard.classList.add("hidden");

  try {
    const result = await getSummary();

    if (!result.ok) {
      showSnackbar(result.error, true);
      return;
    }

    // Populate summary result
    const summaryTextEl = summaryCard.querySelector("p");
    summaryTextEl.innerText = result.data.summary;
    summaryCard.dataset.hash = result.data.hash;

    toggleTools(false);
    summaryCard.classList.remove("hidden");
  } finally {
    // Restore UI state
    loader.classList.add("hidden");
    summarizeBtn.disabled = false;
  }
});


/**
 * Fetch summary from backend API.
 */
async function getSummary() {
  if (!textarea.value.trim()) {
    return {
      ok: false,
      status: 400,
      error: "No text provided!"
    };
  }

  try {
    const response = await fetch("/summarize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: textarea.value.trim() })
    });

    const data = await response.json().catch(() => null);

    return {
      ok: response.ok,
      status: response.status,
      data,
      error: response.ok ? null : data?.error || "Server error"
    };
  } catch (err) {
    return {
      ok: false,
      status: 0, // Network / CORS failure
      error: "Network error!"
    };
  }
}


/* ===============================
   Toolbar Actions
=============================== */

// Copy summary text
copyBtn.addEventListener("click", async () => {
  copyBtn.innerText = "check";

  const result = await copyText(summaryCard.innerText);
  showSnackbar(result.msg, result.error);

  setTimeout(() => {
    copyBtn.innerText = "content_copy";
  }, 1500);
});

// Save summary to library
saveBtn.addEventListener("click", async () => {
  saveBtn.innerText = "check";

  if (!summaryCard.dataset.hash) {
    showSnackbar("No summary to save!", true);
    return;
  }

  const result = await saveSummary(
    summaryCard.innerText,
    summaryCard.dataset.hash
  );
  showSnackbar(result.msg, result.error);

  setTimeout(() => {
    saveBtn.innerText = "bookmark_border";
  }, 1500);
});

// Download summary as text file
downloadBtn.addEventListener("click", () => {
  downloadBtn.innerText = "check";

  const result = downloadSummary(summaryCard.innerText);
  showSnackbar(result.msg, result.error);

  setTimeout(() => {
    downloadBtn.innerText = "download";
  }, 1500);
});


/* ===============================
   Character Limit Handling
=============================== */

const MAX_CHARS = 5000;

textarea.addEventListener("input", () => {
  const length = textarea.value.length;
  charCount.textContent = `${length} / ${MAX_CHARS}`;

  const exceeded = length > MAX_CHARS;

  // Visual feedback for limit overflow
  if (exceeded) {
    textarea.classList.add("limit-exceeded");
    charCount.classList.add("danger");
  } else {
    textarea.classList.remove("limit-exceeded");
    charCount.classList.remove("danger");
  }

  // Prevent submission when limit exceeded
  summarizeBtn.disabled = exceeded;
});