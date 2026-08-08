(() => {
  const script = document.currentScript;
  const widgetId = new URL(script.src).searchParams.get("id");
  if (!widgetId) return;
  const apiBase = new URL(script.src).origin;
  const root = document.createElement("section");
  root.setAttribute("data-widgetforge", widgetId);
  script.insertAdjacentElement("afterend", root);
  fetch(`${apiBase}/public/v1/widgets/${widgetId}/config`)
    .then((r) => r.ok ? r.json() : Promise.reject())
    .then((config) => {
      const title = document.createElement("h3"); title.textContent = config.title; root.append(title);
      const form = document.createElement("form");
      config.form_fields.forEach((definition) => {
        const label = document.createElement("label"); label.textContent = definition.label;
        const input = document.createElement("input"); input.name = definition.name; input.type = definition.type; input.required = definition.required; input.maxLength = definition.max_length;
        label.append(input); form.append(label);
      });
      const trap = document.createElement("input"); trap.name = "website"; trap.tabIndex = -1; trap.autocomplete = "off"; trap.style.cssText = "position:absolute;left:-9999px"; form.append(trap);
      const button = document.createElement("button"); button.type = "submit"; button.textContent = config.button_text; form.append(button);
      const message = document.createElement("p"); root.append(form, message);
      form.addEventListener("submit", async (event) => {
        event.preventDefault(); button.disabled = true;
        const data = new FormData(form); const fields = {};
        config.form_fields.forEach((field) => { fields[field.name] = String(data.get(field.name) || ""); });
        try {
          const response = await fetch(`${apiBase}/public/v1/submissions`, {method: "POST", headers: {"Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID()}, body: JSON.stringify({widget_id: widgetId, fields, website: data.get("website") || ""})});
          message.textContent = response.ok ? "Thanks — your submission was received." : "Please check your details and try again.";
        } catch (_) { message.textContent = "Please try again shortly."; }
        button.disabled = false;
      });
    })
    .catch(() => { root.textContent = "This form is unavailable."; });
})();
