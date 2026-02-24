(function () {
  const btn = document.getElementById("toggleSidebar");
  const sidebar = document.querySelector(".sidebar");
  if (btn && sidebar) {
    btn.addEventListener("click", () => sidebar.classList.toggle("hidden"));
  }

  // Simple table search (optional)
  const search = document.querySelector("[data-table-search]");
  if (search) {
    const table = document.querySelector(search.getAttribute("data-table-search"));
    const rows = table ? Array.from(table.querySelectorAll("tbody tr")) : [];

    search.addEventListener("input", () => {
      const q = search.value.trim().toLowerCase();
      rows.forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
      });
    });
  }

  // Governance - fetch cards if present
  const govBox = document.getElementById("govLiveMetrics");
  if (govBox) {
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    // governance summary
    fetch("/api/governance/")
      .then(r => r.json())
      .then(d => {
        if (!d || d.error) return;
        set("g_sla_health", d.sla_health ?? "-");
        set("g_breach_rate", (d.breach_rate ?? "-") + "%");
        set("g_total_escalations", d.total_escalations ?? "-");
        set("g_avg_resolution_time", (d.avg_resolution_time ?? "-") + "h");
      })
      .catch(() => {});
  }
})();