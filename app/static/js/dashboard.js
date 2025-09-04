// static/js/dashboard.js
import { fetchJson, showToast } from "./helpers.js";

function copyApiKey(keyId) {
  const text = document.getElementById(`key-${keyId}`).innerText;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    // Modern API (works on https:// or http://localhost)
    navigator.clipboard.writeText(text).then(() => {
      showToast("API key copied to clipboard!", "success");
    }).catch(() => {
      showToast("Failed to copy API key", "danger");
    });
  } else {
    // Fallback for plain http or older browsers
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    try {
      document.execCommand("copy");
      showToast("API key copied to clipboard!", "success");
    } catch (err) {
      console.error("Fallback copy failed", err);
      showToast("Failed to copy API key", "danger");
    }

    document.body.removeChild(textarea);
  }
}

async function deleteApiKey(keyId) {
  if (!confirm("Delete this API key?")) return;
  const url = URLS.deleteApiKey.replace("__ID__", keyId);

  const data = await fetchJson(url, { method: "POST" });
  if (!data) return;

  document.getElementById(`key-row-${keyId}`).remove();
  showToast("API key deleted", "success");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-action='copy-key']").forEach(btn => {
    btn.addEventListener("click", () => copyApiKey(btn.dataset.keyId));
  });

  document.querySelectorAll("[data-action='delete-key']").forEach(btn => {
    btn.addEventListener("click", () => deleteApiKey(btn.dataset.keyId));
  });
});
