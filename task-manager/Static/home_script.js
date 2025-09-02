  // ✅ Strike-through + task count
  function updateTaskCount() {
    const total = document.querySelectorAll(".task-text").length;
    const completed = document.querySelectorAll(".task-text.completed").length;
    document.getElementById("task-count").textContent = total - completed;
  }

  document.querySelectorAll(".complete-btn").forEach(cb => {
    cb.addEventListener("change", function () {
      const row = this.closest("tr");
      const taskText = row.querySelector(".task-text");
      taskText.classList.toggle("completed", this.checked);
      updateTaskCount();
    });
  });

  // ✅ Info popup logic
  const backdrop = document.getElementById("backdrop");
  const infoBox = document.getElementById("info-box");
  const infoContent = document.getElementById("info-content");
  const closeBtn = document.querySelector(".info-close");

  function openInfo(task, desc, date) {
    infoContent.innerHTML = ""; // clear

    const title = document.createElement("h4");
    title.textContent = task || "Task";
    infoContent.appendChild(title);

    if ((!desc || desc.trim() === "") && (!date || date.trim() === "")) {
      const p = document.createElement("p");
      p.textContent = "No data found";
      infoContent.appendChild(p);
    } else {
      if (desc && desc.trim() !== "") {
        const p = document.createElement("p");
        p.innerHTML = `<b>Description:</b> ${desc}`;
        infoContent.appendChild(p);
      }
      if (date && date.trim() !== "") {
        const p2 = document.createElement("p");
        p2.innerHTML = `<b>Due Date:</b> ${date}`;
        infoContent.appendChild(p2);
      }
    }

    backdrop.classList.remove("hidden");
    infoBox.classList.remove("hidden");
  }

  function closeInfo() {
    backdrop.classList.add("hidden");
    infoBox.classList.add("hidden");
  }

  document.querySelectorAll(".info-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const row = this.closest("tr");
      openInfo(row.dataset.task, row.dataset.desc, row.dataset.date);
    });
  });

  backdrop.addEventListener("click", closeInfo);
  closeBtn.addEventListener("click", closeInfo);

  // ✅ Initialize task count
  updateTaskCount();