document.addEventListener("DOMContentLoaded", function() {
  // Common CSRF fetch helper
  async function postData(url, data, csrfToken) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  // 🛒 Add to cart
  document.querySelectorAll(".add-to-cart-form").forEach(form => {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const assetId = form.dataset.assetId;
      const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

      try {
        const data = await postData("/add-to-cart/", { asset_id: assetId }, csrfToken);
        if (data.success) {
          alert(data.message);
          const cartCount = document.getElementById("cartCount");
          if (cartCount) cartCount.textContent = data.cart_count;
        } else {
          alert(data.error || "Failed to add item to cart.");
        }
      } catch (err) {
        console.error(err);
        alert("Error adding to cart!");
      }
    });
  });

  // 🔁 Update cart quantity
  document.querySelectorAll(".update-cart-form").forEach(form => {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const assetId = form.dataset.assetId;
      const quantity = form.querySelector("input[name='quantity']").value;
      const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;

      try {
        const data = await postData("/update-cart/", { asset_id: assetId, quantity }, csrf);
        if (data.success) {
          location.reload();
        } else {
          alert(data.error || "Failed to update cart.");
        }
      } catch (err) {
        console.error(err);
        alert("Error updating cart!");
      }
    });
  });

  // ❌ Remove from cart
  document.querySelectorAll(".remove-from-cart").forEach(btn => {
    btn.addEventListener("click", async () => {
      const assetId = btn.dataset.assetId;
      const csrf = btn.dataset.csrf;

      if (!confirm("Are you sure you want to remove this item?")) return;

      try {
        const data = await postData("/delete-from-cart/", { asset_id: assetId }, csrf);
        if (data.success) {
          location.reload();
        } else {
          alert(data.error || "Failed to remove item.");
        }
      } catch (err) {
        console.error(err);
        alert("Error removing item from cart!");
      }
    });
  });
});
