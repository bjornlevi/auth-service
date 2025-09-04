// static/js/helpers.js

/**
 * Show a Bootstrap toast with a message
 * @param {string} message
 * @param {"success"|"danger"|"warning"} type
 */
export function showToast(message, type = "success") {
  const toastEl = document.getElementById("actionToast") || document.getElementById("dashboardToast");
  const toastBody = document.getElementById("toastMessage") || document.getElementById("dashboardToastMessage");

  if (!toastEl || !toastBody) {
    console.warn("Toast elements missing in DOM");
    return;
  }

  toastBody.innerText = message;

  toastEl.classList.remove("text-bg-success", "text-bg-danger", "text-bg-warning");
  toastEl.classList.add("text-bg-" + type);

  const toast = new bootstrap.Toast(toastEl);
  toast.show();
}

/**
 * Fetch JSON with sensible defaults for auth-service
 * - Always include cookies
 * - Add X-Requested-With
 * - Handle redirects to login
 */
export async function fetchJson(url, options = {}) {
  options.headers = options.headers || {};
  options.credentials = "include"; // send cookies
  options.headers["X-Requested-With"] = "XMLHttpRequest";

  try {
    const res = await fetch(url, options);
    const contentType = res.headers.get("content-type") || "";

    if (contentType.indexOf("application/json") === -1) {
      const text = await res.text();
      if (text.toLowerCase().includes("login")) {
        showToast("⚠️ You must log in first", "warning");
        window.location.href = URLS.login;
        return null;
      }
      throw new Error("Unexpected non-JSON response");
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ("Request failed with " + res.status));

    return data;
  } catch (err) {
    showToast(err.message || "Network error", "danger");
    return null;
  }
}
