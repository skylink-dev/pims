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

  // 🧩 Helper: show success/error messages
  function showMessage(msgBox, text, isSuccess = true) {
    msgBox.textContent = text;
    msgBox.classList.remove("text-green-600", "text-red-600");
    msgBox.classList.add(isSuccess ? "text-green-600" : "text-red-600");
    msgBox.style.opacity = "1";

    // Auto hide after 2s
    setTimeout(() => {
      msgBox.style.opacity = "0";
      setTimeout(() => {
        msgBox.textContent = "";
        msgBox.style.opacity = "1";
      }, 500);
    }, 2000);
  }

  // 🛒 Add to Cart
  document.querySelectorAll(".add-to-cart-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const assetId = form.dataset.assetId;
      const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
      const quantity = parseInt(form.querySelector("[name=quantity]").value) || 1;

      let msgBox = form.querySelector(".cart-message");
      if (!msgBox) {
        msgBox = document.createElement("div");
        msgBox.className =
          "cart-message mt-2 text-sm font-medium transition-opacity duration-500";
        form.appendChild(msgBox);
      }

      try {
        const data = await postData("/add-to-cart/", { asset_id: assetId, quantity }, csrfToken);
        if (data.success) {
          showMessage(msgBox, data.message || "Item added to cart!", true);

          // Update cart count if available
          const cartCount = document.getElementById("cart-count");
          console.log(cartCount);
          console.log(data);
          if (cartCount){
            cartCount.textContent = data.;
          }
        } else {
          showMessage(msgBox, data.error || "Failed to add item to cart.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(msgBox, "Error adding to cart!", false);
      }
    });
  });

  // 🔁 Update Cart Quantity
  document.querySelectorAll(".update-cart-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const assetId = form.dataset.assetId;
      const quantity = form.querySelector("input[name='quantity']").value;
      const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;

      let msgBox = form.querySelector(".cart-message");
      if (!msgBox) {
        msgBox = document.createElement("div");
        msgBox.className =
          "cart-message mt-2 text-sm font-medium transition-opacity duration-500";
        form.appendChild(msgBox);
      }

      try {
        const data = await postData("/update-cart/", { asset_id: assetId, quantity }, csrf);
        if (data.success) {
          showMessage(msgBox, "Quantity updated successfully!", true);
        } else {
          showMessage(msgBox, data.error || "Failed to update cart.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(msgBox, "Error updating cart!", false);
      }
    });
  });

  // ❌ Remove from Cart
  document.querySelectorAll(".remove-from-cart").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const assetId = btn.dataset.assetId;
      const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
      const row = btn.closest("tr");

      let msgBox = row.querySelector(".cart-message");
      if (!msgBox) {
        msgBox = document.createElement("div");
        msgBox.className =
          "cart-message mt-2 text-sm font-medium transition-opacity duration-500";
        row.appendChild(msgBox);
      }

      try {
        const data = await postData("/delete-from-cart/", { asset_id: assetId }, csrf);
        if (data.success) {
          showMessage(msgBox, "Item removed successfully!", true);
          row.style.transition = "opacity 0.5s ease";
          row.style.opacity = "0";
          setTimeout(() => row.remove(), 500);
        } else {
          showMessage(msgBox, data.error || "Failed to remove item.", false);
        }
      } catch (err) {
        console.error(err);
        showMessage(msgBox, "Error removing item!", false);
      }
    });
  });
});
