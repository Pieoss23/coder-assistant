(() => {
  const splash = document.querySelector("[data-splash]");
  if (!splash) return;
  window.setTimeout(() => {
    window.location.assign("/home");
  }, 1400);
})();
