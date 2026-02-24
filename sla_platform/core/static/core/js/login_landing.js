(function () {
  // Smooth scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href");
      if (!href || href === "#") return;

      const target = document.querySelector(href);
      if (!target) return;

      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  // Role tabs logic
  const roleInput = document.getElementById("roleInput");
  const roleHint = document.getElementById("roleHint");
  const tabs = document.querySelectorAll(".role-tab");

  if (!roleInput || tabs.length === 0) return;

  const hints = {
    client: "Client can create tickets and track SLA status.",
    engineer: "Engineer can view assigned tickets and update ticket status.",
    admin: "Admin can access governance dashboards and system insights."
  };

  function setRole(role) {
    roleInput.value = role;
    tabs.forEach(t => t.classList.toggle("active", t.dataset.role === role));
    if (roleHint) roleHint.textContent = hints[role] || "";
  }

  tabs.forEach(btn => btn.addEventListener("click", () => setRole(btn.dataset.role)));

  // Default role
  setRole(roleInput.value || "client");
})();