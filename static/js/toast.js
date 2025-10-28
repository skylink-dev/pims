function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");

  // Style based on type (success, error, info)
  const bgColor =
    type === "success"
      ? "bg-green-600"
      : type === "error"
      ? "bg-red-600"
      : "bg-blue-600";

  toast.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg transform transition-all duration-500 opacity-0 translate-y-2`;
  toast.innerText = message;

  container.appendChild(toast);

  // Fade in
  setTimeout(() => {
    toast.classList.remove("opacity-0", "translate-y-2");
  }, 100);

  // Fade out and remove after 3 seconds
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 500);
  }, 3000);
}
