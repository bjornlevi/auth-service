// static/js/users.js
import { fetchJson, showToast } from "./helpers.js";

async function toggleAdmin(userId) {
  const url = URLS.toggleAdmin.replace("__ID__", userId);
  const data = await fetchJson(url, { method: "POST" });
  if (!data) return;

  if (data.success) {
    document.getElementById(`user-admin-${userId}`).innerText = data.is_admin ? "✅" : "❌";
    showToast(`User ${data.username} is now ${data.is_admin ? "Admin" : "User"}`, "success");

    const btn = document.getElementById(`toggle-btn-${userId}`);
    if (btn) {
      btn.textContent = data.is_admin ? "Demote" : "Promote";
      btn.classList.remove("btn-primary", "btn-warning");
      btn.classList.add(data.is_admin ? "btn-warning" : "btn-primary");
    }
  }
}

async function deleteUser(userId, username) {
  if (!confirm(`Delete user ${username}?`)) return;

  const url = URLS.deleteUser.replace("__ID__", userId);
  const data = await fetchJson(url, { method: "POST" });
  if (!data) return;

  if (data.success) {
    document.getElementById(`user-row-${userId}`).remove();
    showToast(`User ${username} deleted`, "success");
  }
}

async function requestReset(userId, username) {
  const url = URLS.resetUser.replace("__ID__", userId);
  const data = await fetchJson(url, { method: "POST" });
  if (!data) return;

  if (data.reset_url) {
    document.getElementById("resetMessage").innerText = `Share this reset link with ${username}:`;
    document.getElementById("resetLink").value = data.reset_url;

    const modal = new bootstrap.Modal(document.getElementById("resetModal"));
    modal.show();
  }
}

function copyResetLink() {
  const text = document.getElementById("resetLink").value;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Reset link copied to clipboard!", "success");
  });
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-action='toggle-admin']").forEach(btn => {
    btn.addEventListener("click", () => toggleAdmin(btn.dataset.userId));
  });

  document.querySelectorAll("[data-action='delete']").forEach(btn => {
    btn.addEventListener("click", () => deleteUser(btn.dataset.userId, btn.dataset.username));
  });

  document.querySelectorAll("[data-action='reset']").forEach(btn => {
    btn.addEventListener("click", () => requestReset(btn.dataset.userId, btn.dataset.username));
  });

  document.getElementById("copyResetBtn")?.addEventListener("click", copyResetLink);
});
