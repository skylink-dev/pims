document.addEventListener("DOMContentLoaded", function() {
    const forms = document.querySelectorAll(".add-to-cart-form");

    forms.forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            const assetId = form.dataset.assetId;
            const csrfToken = form.querySelector("input[name='csrfmiddlewaretoken']").value;

            fetch("/add-to-cart/", {   // <-- URL is just /add-to-cart/
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ asset_id: assetId })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success){
                    alert(data.message);
                    const cartCount = document.getElementById("cartCount");
                    if(cartCount) cartCount.textContent = data.cart_count;
                } else {
                    alert(data.error);
                }
            })
            .catch(err => {
                console.error(err);
                alert("Error adding to cart!");
            });
        });
    });
});
