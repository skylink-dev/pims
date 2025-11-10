document.addEventListener("DOMContentLoaded", function () {
  // 🔒 Common helper for POST with CSRF
  async function postData(url, data, csrfToken) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    });
    return response.json();
  }

  // 🧩 Modal Popup Setup
  function createPopupModal() {
    let modal = document.getElementById("popup-modal");
    if (modal) return modal; // prevent duplicates

    modal = document.createElement("div");
    modal.id = "popup-modal";
    modal.className =
      "fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 hidden";
    modal.innerHTML = `
      <div class="bg-white rounded-2xl shadow-lg max-w-sm w-full mx-4 p-6 text-center transform transition-all scale-95 opacity-0">
        <div id="popup-icon" class="text-5xl mb-3"></div>
        <h2 id="popup-message" class="text-lg font-semibold"></h2>
        <button id="popup-close" class="mt-5 px-5 py-2 rounded-md bg-gray-800 text-white hover:bg-gray-700">OK</button>
      </div>
    `;
    document.body.appendChild(modal);

    const closeBtn = modal.querySelector("#popup-close");
    closeBtn.addEventListener("click", () => hidePopupModal());
    return modal;
  }

  function showPopupModal(message, isSuccess = true, reload = false) {
    const modal = createPopupModal();
    const msgBox = modal.querySelector("#popup-message");
    const icon = modal.querySelector("#popup-icon");
    const contentBox = modal.querySelector("div > div");

    msgBox.textContent = message;
    icon.innerHTML = isSuccess
      ? "✅"
      : "❌";
    icon.className = isSuccess ? "text-green-500 text-5xl mb-3" : "text-red-500 text-5xl mb-3";

    modal.classList.remove("hidden");
    setTimeout(() => {
      contentBox.classList.remove("opacity-0", "scale-95");
      contentBox.classList.add("opacity-100", "scale-100");
    }, 10);

    // Auto close after 2s
    setTimeout(() => hidePopupModal(reload), 2000);
  }

  function hidePopupModal(reload = false) {
    const modal = document.getElementById("popup-modal");
    if (!modal) return;
    const contentBox = modal.querySelector("div > div");

    contentBox.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      modal.classList.add("hidden");
      if (reload) window.location.reload();
    }, 300);
  }

  // Override existing inline message function to use popup
  function showMessage(msgBox, text, isSuccess = true, reload = false) {
    showPopupModal(text, isSuccess, reload);
  }

  // 🛒 Add to Cart
  document.querySelectorAll(".add-to-cart-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const assetId = form.dataset.assetId;
      const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
      const quantity = parseInt(form.querySelector("[name=quantity]").value) || 1;

      try {
        const data = await postData("/add-to-cart/", { asset_id: assetId, quantity }, csrfToken);
        if (data.success) {
          showMessage(null, data.message || "Item added to cart!", true, true);
          const cartCount = document.getElementById("cart-count");
          if (cartCount) cartCount.textContent = data.cart_count;
        } else {
          showMessage(null, data.error || "Failed to add item to cart.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(null, "Error adding to cart!", false);
      }
    });
  });

  // 🔁 Update Cart Quantity
  document.querySelectorAll(".quantity-control").forEach((control) => {
    const assetId = control.dataset.assetId;
    const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const quantityDisplay = control.querySelector(".quantity-display");
    const plusBtn = control.querySelector(".plus-btn");
    const minusBtn = control.querySelector(".minus-btn");

    const updateQuantity = async (newQuantity) => {
      if (newQuantity < 1) return;

      plusBtn.disabled = true;
      minusBtn.disabled = true;

      try {
        const data = await postData("/update-cart/", { asset_id: assetId, quantity: newQuantity }, csrf);
        if (data.success) {
          quantityDisplay.textContent = newQuantity;
          const totalPriceEl = document.getElementById("total-price");
          if (totalPriceEl && data.new_total_price !== undefined)
            totalPriceEl.textContent = `₹${data.new_total_price}`;
        } else {
          showMessage(null, data.error || "Failed to update cart.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(null, "Error updating quantity!", false);
      } finally {
        setTimeout(() => {
          plusBtn.disabled = false;
          minusBtn.disabled = false;
        }, 800);
      }
    };

    plusBtn.addEventListener("click", () => {
      const currentQty = parseInt(quantityDisplay.textContent);
      updateQuantity(currentQty + 1);
    });
    minusBtn.addEventListener("click", () => {
      const currentQty = parseInt(quantityDisplay.textContent);
      updateQuantity(currentQty - 1);
    });
  });

  // ❌ Remove from Cart
  document.querySelectorAll(".remove-from-cart").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const assetId = btn.dataset.assetId;
      const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
      const row = btn.closest("tr") || btn.closest(".cart-card");

      try {
        const data = await postData("/delete-from-cart/", { asset_id: assetId }, csrf);
        if (data.success) {
          row.style.transition = "opacity 0.4s ease";
          row.style.opacity = "0";
          setTimeout(() => row.remove(), 400);
          const totalPriceEl = document.getElementById("total-price");
          if (totalPriceEl && data.new_total_price !== undefined)
            totalPriceEl.textContent = `₹${data.new_total_price.toFixed(2)}`;
          const cartCount = document.getElementById("cart-count");
          if (cartCount && data.cart_count !== undefined)
            cartCount.textContent = data.cart_count;
          showMessage(null, data.message || "Item removed successfully!", true);
        } else {
          showMessage(null, data.error || "Failed to remove item.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(null, "Error removing item!", false);
      }
    });
  });
});
