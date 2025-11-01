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
  function showMessage(msgBox, text, isSuccess = true,reload=false) {
    msgBox.textContent = text;
    msgBox.classList.remove("text-green-600", "text-red-600");
    msgBox.classList.add(isSuccess ? "text-green-600" : "text-red-600");
    msgBox.style.opacity = "1";
    console.log(isSuccess)
    if (isSuccess) window.location.reload();

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
          showMessage(msgBox, data.message || "Item added to cart!", true,true);

          // Update cart count if available
          const cartCount = document.getElementById("cart-count");
          console.log(cartCount);
          console.log(data);
          if (cartCount){
            cartCount.textContent = data.cart_count;
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
 document.querySelectorAll(".quantity-control").forEach((control) => {
    const assetId = control.dataset.assetId;
    const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const quantityDisplay = control.querySelector(".quantity-display");
    const plusBtn = control.querySelector(".plus-btn");
    const minusBtn = control.querySelector(".minus-btn");

    let msgBox = control.querySelector(".cart-message");
    if (!msgBox) {
      msgBox = document.createElement("div");
      msgBox.className = "cart-message mt-1 text-sm font-medium transition-opacity duration-500";
      control.appendChild(msgBox);
    }
const updateQuantity = async (newQuantity) => {
  if (newQuantity < 1) return;

  plusBtn.disabled = true;
  minusBtn.disabled = true;

  try {
    const data = await postData("/update-cart/", { asset_id: assetId, quantity: newQuantity }, csrf);
    if (data.success) {
      quantityDisplay.textContent = newQuantity;

      // 💰 Update total price dynamically
      const totalPriceEl = document.getElementById("total-price");
      if (totalPriceEl && data.new_total_price !== undefined) {
        totalPriceEl.textContent = `₹${data.new_total_price}`;
      }

      // Optional: Success message
      // showMessage(msgBox, "Quantity updated!", true);
    } else {
      showMessage(msgBox, data.error || "Failed to update cart.", false);
    }
  } catch (err) {
    console.error(err);
    showMessage(msgBox, "Error updating quantity!", false);
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
        // 🧹 Fade out removed row
        row.style.transition = "opacity 0.4s ease";
        row.style.opacity = "0";
        setTimeout(() => row.remove(), 400);

        // 💰 Update total price dynamically
        const totalPriceEl = document.getElementById("total-price");
        if (totalPriceEl && data.new_total_price !== undefined) {
          totalPriceEl.textContent = `₹${data.new_total_price.toFixed(2)}`;
        }

        // 🛒 Update cart count if shown
        const cartCount = document.getElementById("cart-count");
        if (cartCount && data.cart_count !== undefined) {
          cartCount.textContent = data.cart_count;
        }

        showMessage(msgBox, data.message || "Item removed successfully!", true);
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
