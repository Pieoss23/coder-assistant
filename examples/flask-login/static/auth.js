document.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-auth-form]");
  if (!form) return;
  const button = form.querySelector("button[type='submit']");
  if (!button) return;
  button.disabled = true;
  button.textContent = button.dataset.submitLabel || "In corso…";
});
