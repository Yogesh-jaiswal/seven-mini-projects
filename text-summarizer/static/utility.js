/* ===============================
   Snackbar Notifications
=============================== */

/**
 * Display a snackbar message.
 * Supports success and error modes.
 */
function showSnackbar(message, errMode = false, duration = 3000) {
  const snackbar = document.getElementById("snackbar");
  const msg = document.getElementById("snackbar-message");
  const img = document.getElementById("snackbar-img");

  // Accessibility role based on message type
  snackbar.setAttribute("role", errMode ? "alert" : "status");

  msg.textContent = message;

  // Reset previous state
  snackbar.classList.remove("active", "error");

  if (errMode) {
    img.src = "../static/warning.png";
    snackbar.classList.add("active", "error");
  } else {
    img.src = "../static/check.png";
    snackbar.classList.add("active");
  }

  // Auto-hide snackbar
  setTimeout(() => {
    snackbar.classList.remove("active", "error");
  }, duration);
}

/* Manual snackbar dismissal */
const closeBtn = document.querySelector(".closebar");

closeBtn.addEventListener("click", () => {
  const snackbar = document.getElementById("snackbar");
  snackbar.classList.remove("active", "error");
});


/* ===============================
   Clipboard Utility
=============================== */

/**
 * Copy text to clipboard.
 */
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return {
      msg: "Copied to clipboard!",
      error: false
    };
  } catch (err) {
    return {
      msg: "Copy failed!",
      error: true
    };
  }
}


/* ===============================
   Summary Persistence
=============================== */

/**
 * Save a summary to the backend.
 */
async function saveSummary(text, hash) {
  if (!text) {
    return {
      msg: "Summary is empty!",
      error: true
    };
  }

  try {
    const response = await fetch("/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ summary: text, hash: hash })
    });

    await response.json();

    if (response.ok) {
      return {
        msg: "Summary saved!",
        error: false
      };
    } else {
      return {
        msg: "Error occured!",
        error: true
      };
    }
  } catch (err) {
    return {
      msg: "Network error!",
      error: true
    };
  }
}


/* ===============================
   Download Utility
=============================== */

/**
 * Download summary text as a .txt file.
 */
function downloadSummary(text) {
  if (!text.trim()) {
    return {
      msg: "No summary found!",
      error: true
    };
  }

  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  // Temporary anchor for download
  const a = document.createElement("a");
  a.href = url;
  a.download = `summary-${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();

  // Cleanup
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  return {
    msg: "Summary downloaded!",
    error: false
  };
}


/* ===============================
   Delete Utility
=============================== */

/**
 * Delete a saved summary by ID.
 */
async function deleteSummary(id) {
  try {
    const response = await fetch(`/delete/${id}`, {
      method: "DELETE"
    });

    await response.json();

    if (response.ok) {
      return {
        msg: "Summary deleted!",
        error: false
      };
    } else {
      return {
        msg: "Summary not found!",
        error: true
      };
    }
  } catch (err) {
    return {
      msg: "Network error!",
      error: true
    };
  }
}