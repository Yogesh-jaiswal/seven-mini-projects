/* ===============================
   Saved Item Actions
=============================== */

const savedItems = document.querySelectorAll(".saved-item");

savedItems.forEach(savedItem => {
  // Action buttons within each saved summary
  const copyBtn = savedItem.querySelector(".copy");
  const downloadBtn = savedItem.querySelector(".download");
  const deleteBtn = savedItem.querySelector(".delete");

  // Summary content element
  const content = savedItem.querySelector(".content");

  /* ---------- Copy Summary ---------- */
  copyBtn.addEventListener("click", async () => {
    copyBtn.innerText = "check";

    const result = await copyText(content.innerText);
    showSnackbar(result.msg, result.error);

    // Restore icon after feedback
    setTimeout(() => {
      copyBtn.innerText = "content_copy";
    }, 1500);
  });

  /* ---------- Download Summary ---------- */
  downloadBtn.addEventListener("click", () => {
    downloadBtn.innerText = "check";

    const result = downloadSummary(content.innerText);
    showSnackbar(result.msg, result.error);

    // Restore icon after feedback
    setTimeout(() => {
      downloadBtn.innerText = "download";
    }, 1500);
  });

  /* ---------- Delete Summary ---------- */
  deleteBtn.addEventListener("click", async () => {
    deleteBtn.innerText = "check";

    const result = await deleteSummary(savedItem.dataset.id);

    if (!result.error) {
      // Remove item from DOM and refresh state
      savedItem.remove();
      window.location.reload();
    }

    showSnackbar(result.msg, result.error);

    // Restore icon after feedback
    setTimeout(() => {
      deleteBtn.innerText = "delete";
    }, 1500);
  });
});


/* ===============================
   Expand / Collapse Logic
=============================== */

const COLLAPSED_HEIGHT = 150;

document.querySelectorAll(".content-card").forEach(card => {
  const content = card.querySelector(".content");
  const toggle = card.querySelector(".toggle");
  const divider = card.querySelector(".divider");

  if (!content || !toggle) return;

  // Measure full rendered content height
  const fullHeight = content.scrollHeight;

  // Only enable collapsing if content exceeds threshold
  if (fullHeight > COLLAPSED_HEIGHT) {
    content.classList.add("collapsed");
    toggle.style.display = "inline-flex";
  } else {
    // Hide unnecessary UI for short content
    toggle.style.display = "none";
    divider.style.display = "none";
    return;
  }

  /* ---------- Toggle Expand / Collapse ---------- */
  toggle.addEventListener("click", () => {
    const isCollapsed = content.classList.toggle("collapsed");
    toggle.classList.toggle("expanded", !isCollapsed);
  });
});