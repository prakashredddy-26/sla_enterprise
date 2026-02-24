// core/static/core/js/app.js
document.addEventListener("DOMContentLoaded", () => {
  /* ===========================
     LOGIN ROLE TABS (UI only)
     =========================== */
  const tabs = document.querySelectorAll("[data-role-tab]");
  const roleHint = document.getElementById("roleHint");

  if (tabs && tabs.length > 0) {
    const hints = {
      client: "Client can create tickets and track status.",
      engineer: "Engineer can view assigned tickets and update status.",
      admin: "Admin can view Governance dashboards.",
    };

    const setActive = (role) => {
      tabs.forEach((btn) => {
        const active = btn.dataset.roleTab === role;
        btn.classList.toggle("active", active);
      });
      if (roleHint) roleHint.textContent = hints[role] || "";
    };

    setActive("client");
    tabs.forEach((btn) => btn.addEventListener("click", () => setActive(btn.dataset.roleTab)));
  }

  /* ===========================
     SIDEBAR TOGGLE (Client/Admin/Engineer)
     =========================== */
  const sidebar = document.getElementById("sidebar") || document.querySelector(".sidebar");
  const toggleBtn = document.getElementById("toggleSidebar");

  const applySidebarState = (collapsed) => {
    if (!sidebar) return;
    sidebar.classList.toggle("collapsed", collapsed);

    // for mobile, use "hidden"
    if (window.innerWidth <= 980) {
      sidebar.classList.toggle("hidden", collapsed);
    }
  };

  // restore state
  const saved = localStorage.getItem("sla_sidebar_collapsed");
  if (saved === "1") applySidebarState(true);

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      const isCollapsed = sidebar.classList.contains("collapsed") || sidebar.classList.contains("hidden");

      // On mobile toggle hidden, on desktop toggle collapsed
      if (window.innerWidth <= 980) {
        sidebar.classList.toggle("hidden");
        localStorage.setItem("sla_sidebar_collapsed", sidebar.classList.contains("hidden") ? "1" : "0");
      } else {
        sidebar.classList.toggle("collapsed");
        localStorage.setItem("sla_sidebar_collapsed", sidebar.classList.contains("collapsed") ? "1" : "0");
      }
    });
  }

  window.addEventListener("resize", () => {
    if (!sidebar) return;
    const savedState = localStorage.getItem("sla_sidebar_collapsed") === "1";
    if (window.innerWidth > 980) {
      sidebar.classList.remove("hidden");
      sidebar.classList.toggle("collapsed", savedState);
    } else {
      sidebar.classList.toggle("hidden", savedState);
      sidebar.classList.remove("collapsed");
    }
  });

  /* ===========================
     PROFILE MENU (Avatar click)
     =========================== */
  const profileBtn = document.getElementById("profileBtn");
  const profileMenu = document.getElementById("profileMenu");

  const closeProfile = () => {
    if (!profileMenu || !profileBtn) return;
    profileMenu.classList.remove("open");
    profileMenu.setAttribute("aria-hidden", "true");
    profileBtn.setAttribute("aria-expanded", "false");
  };

  const openProfile = () => {
    if (!profileMenu || !profileBtn) return;
    profileMenu.classList.add("open");
    profileMenu.setAttribute("aria-hidden", "false");
    profileBtn.setAttribute("aria-expanded", "true");
  };

  if (profileBtn && profileMenu) {
    profileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = profileMenu.classList.contains("open");
      if (isOpen) closeProfile();
      else openProfile();
    });

    document.addEventListener("click", (e) => {
      if (!profileMenu.contains(e.target) && e.target !== profileBtn) closeProfile();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeProfile();
    });
  }

  /* ===========================
     TABLE SEARCH (supports data-table-search="#id")
     =========================== */
  const searchers = document.querySelectorAll("[data-table-search]");
  searchers.forEach((inp) => {
    const selector = inp.getAttribute("data-table-search");
    const table = selector ? document.querySelector(selector) : null;
    if (!table) return;

    const tbody = table.querySelector("tbody");
    const getRows = () => Array.from((tbody || table).querySelectorAll("tr"));

    const filter = () => {
      const q = (inp.value || "").trim().toLowerCase();
      getRows().forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(q) ? "" : "none";
      });
    };

    inp.addEventListener("input", filter);
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        inp.value = "";
        filter();
      }
    });
  });

  /* ===========================
     ENGINEER DASHBOARD KPI COUNTS (no backend changes)
     =========================== */
  const kpiResolved = document.getElementById("kpiResolved");
  const kpiActive = document.getElementById("kpiActive");
  const kpiBreached = document.getElementById("kpiBreached");
  const dashTable = document.getElementById("dashTable");

  if (dashTable && (kpiResolved || kpiActive || kpiBreached)) {
    const rows = Array.from(dashTable.querySelectorAll("tbody tr"));

    let resolved = 0;
    let breached = 0;
    let active = 0;

    rows.forEach((r) => {
      const statusCell = r.querySelector(".ticket-status-cell");
      const txt = (statusCell ? statusCell.innerText : r.innerText).toUpperCase();

      if (txt.includes("RESOLVED")) resolved += 1;
      if (txt.includes("BREACHED")) breached += 1;

      // Active = anything not resolved (includes NEW / IN_PROGRESS / REOPENED / BREACHED etc.)
      if (!txt.includes("RESOLVED")) active += 1;
    });

    if (kpiResolved) kpiResolved.textContent = String(resolved);
    if (kpiBreached) kpiBreached.textContent = String(breached);
    if (kpiActive) kpiActive.textContent = String(active);
  }

  /* ===========================
     DASHBOARD SEARCH (fallback - keeps your old behavior)
     =========================== */
  const searchInput =
    document.querySelector('input[placeholder*="Search tickets" i]') ||
    document.querySelector("#ticketSearch") ||
    document.querySelector(".ticket-search") ||
    document.querySelector('input[name="search"]');

  const ticketTable =
    document.querySelector("#ticketTable") ||
    document.querySelector(".ticket-table") ||
    document.querySelector("table");

  if (searchInput && ticketTable && !searchInput.hasAttribute("data-table-search")) {
    const tbody = ticketTable.querySelector("tbody");
    const rows = Array.from((tbody || ticketTable).querySelectorAll("tr"));

    const filterRows = () => {
      const q = (searchInput.value || "").trim().toLowerCase();
      rows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(q) ? "" : "none";
      });
    };

    searchInput.addEventListener("input", filterRows);
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        searchInput.value = "";
        filterRows();
      }
    });
  }
});