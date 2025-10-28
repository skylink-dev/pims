document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("mapModal");
  const openButtons = document.querySelectorAll(".open-map-modal");
  const cancelBtn = document.getElementById("cancelMap");
  const confirmBtn = document.getElementById("confirmMap");
  const searchBtn = document.getElementById("btnSearch");
  const searchInput = document.getElementById("searchPhone");
  const searchStatus = document.getElementById("searchStatus");
  const customerCard = document.getElementById("customerCard");
  const custName = document.getElementById("cust_name");
  const custPhone = document.getElementById("cust_phone");
  const custEmail = document.getElementById("cust_email");
  const custAddress = document.getElementById("cust_address");

  let selectedSerialId = null;
  let selectedCustomer = null;

  // ✅ Open modal
  openButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedSerialId = btn.dataset.serial;
      modal.classList.remove("hidden");
      customerCard.classList.add("hidden");
      confirmBtn.classList.add("hidden");
      searchStatus.textContent = "";
      searchInput.value = "";
    });
  });

  // ✅ Close modal
  cancelBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  // ✅ Handle search
  searchBtn.addEventListener("click", async () => {
    const phone = searchInput.value.trim();
    if (!phone) {
      searchStatus.textContent = "Please enter a phone number.";
      return;
    }

    searchStatus.textContent = "Searching...";
    customerCard.classList.add("hidden");
    confirmBtn.classList.add("hidden");

    try {
      const response = await fetch(
        `/customer-mapping/get-customer/?phone=${encodeURIComponent(phone)}`
      );
      const data = await response.json();

      if (data.customers && data.customers.length > 0) {
        searchStatus.textContent = `${data.customers.length} customer(s) found. Select one below.`;

        let selectHtml = `<select id="customerSelect" class="border p-2 rounded w-full mt-2">`;
        selectHtml += `<option value="">Select Customer</option>`;
        data.customers.forEach((cust) => {
          selectHtml += `<option 
              value="${cust.id}" 
              data-name="${cust.name}" 
              data-phone="${cust.phone}" 
              data-email="${cust.email}" 
              data-city="${cust.city}"
              data-username="${cust.username}">
              ${cust.name} (${cust.username}) - ${cust.status} - ${cust.plan}
            </option>`;
        });
        selectHtml += `</select>`;
        searchStatus.innerHTML = selectHtml;

        // ✅ Listen for select change
        document.getElementById("customerSelect").addEventListener("change", (e) => {
          const opt = e.target.selectedOptions[0];
          if (!opt.value) return;

          selectedCustomer = {
            id: opt.value,
            name: opt.dataset.name,
            phone: opt.dataset.phone,
            email: opt.dataset.email,
            address: opt.dataset.city,
            username: opt.dataset.username, // ✅ SkyID
          };

          custName.textContent = `${selectedCustomer.name} (${selectedCustomer.username})`; // ✅ show SkyID
          custPhone.textContent = selectedCustomer.phone;
          custEmail.textContent = selectedCustomer.email;
          custAddress.textContent = selectedCustomer.address;
          customerCard.classList.remove("hidden");
          confirmBtn.classList.remove("hidden");
        });
      } else {
        searchStatus.textContent = "No customer found.";
      }
    } catch (err) {
      console.error(err);
      searchStatus.textContent = "Error fetching customer.";
    }
  });

  // ✅ Confirm assignment
  confirmBtn.addEventListener("click", async () => {
    if (!selectedCustomer || !selectedSerialId) {
      showToast("Please select a customer first!", "error");
      return;
    }

    const payload = {
      serial_id: selectedSerialId,
      name: selectedCustomer.name,
      phone: selectedCustomer.phone,
      email: selectedCustomer.email,
      address: selectedCustomer.address,
      username: selectedCustomer.username, // ✅ include SkyID in request
    };

    try {
      const response = await fetch("/customer-mapping/assign/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (result.success) {
        showToast("✅ Asset successfully mapped!", "success");
        modal.classList.add("hidden");

        // Optionally refresh page after 1.5s
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast(result.message || "Mapping failed.", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Failed to map asset!", "error");
    }
  });

  // ✅ CSRF helper
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
