const page = document.body.dataset.page;

const api = {
  async get(url) {
    const res = await fetch(url);
    return res.json();
  },
  async post(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    return res.json();
  },
};

function qs(id) {
  return document.getElementById(id);
}

function createRowInput(value = "") {
  const wrapper = document.createElement("div");
  wrapper.className = "row-inline";
  const input = document.createElement("input");
  input.value = value;
  const remove = document.createElement("button");
  remove.className = "btn btn--ghost";
  remove.textContent = "Remove";
  remove.addEventListener("click", () => wrapper.remove());
  wrapper.appendChild(input);
  wrapper.appendChild(remove);
  return wrapper;
}

function createItemRow() {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input class="item-code" placeholder="00015" /></td>
    <td><input class="item-desc" placeholder="Auto from masterlist" /></td>
    <td><input class="item-width" type="number" min="0" /></td>
    <td><input class="item-length" type="number" min="0" /></td>
    <td><input class="item-qty" type="number" min="1" /></td>
    <td><button class="btn btn--ghost item-remove">Remove</button></td>
  `;
  tr.querySelector(".item-remove").addEventListener("click", () => tr.remove());
  return tr;
}

async function initCreateOrder() {
  const poList = qs("po-list");
  const supplierList = qs("supplier-list");
  const items = qs("item-rows");
  const resultBox = qs("result-box");

  qs("add-po").addEventListener("click", () => {
    poList.appendChild(createRowInput());
  });
  qs("add-supplier-do").addEventListener("click", () => {
    supplierList.appendChild(createRowInput());
  });
  qs("add-item").addEventListener("click", () => {
    const row = createItemRow();
    row.querySelector(".item-code").addEventListener("blur", () =>
      loadItemDescription(row)
    );
    row.querySelector(".item-code").addEventListener("change", () =>
      loadItemDescription(row)
    );
    items.appendChild(row);
  });

  poList.appendChild(createRowInput());
  supplierList.appendChild(createRowInput());
  const firstRow = createItemRow();
  firstRow.querySelector(".item-code").addEventListener("blur", () =>
    loadItemDescription(firstRow)
  );
  firstRow.querySelector(".item-code").addEventListener("change", () =>
    loadItemDescription(firstRow)
  );
  items.appendChild(firstRow);

  let currentJo = "";

  function collectList(container) {
    return Array.from(container.querySelectorAll("input"))
      .map((input) => input.value.trim())
      .filter((value) => value.length > 0);
  }

  async function loadClientSnapshot() {
    const code = qs("client-code").value.trim();
    if (!code) return;
    const res = await api.get(`/api/clients/${encodeURIComponent(code)}`);
    if (!res.ok) {
      resultBox.textContent = res.error || "Client not found";
      return;
    }
    const data = res.data;
    if (!qs("client-name").value.trim()) {
      qs("client-name").value = data.client_name || "";
    }
    qs("client-address").value = data.delivery_address || "";
    qs("client-pic").value = data.client_pic || "";
    qs("client-contact").value = data.client_contact || "";
  }

  async function loadItemDescription(row) {
    const codeInput = row.querySelector(".item-code");
    const descInput = row.querySelector(".item-desc");
    const code = codeInput.value.trim();
    if (!code) return;
    const res = await api.get(`/api/items/${encodeURIComponent(code)}`);
    if (!res.ok) {
      resultBox.textContent = res.error || "Item not found";
      return;
    }
    if (!descInput.value.trim()) {
      descInput.value = res.data.item_description || "";
    }
  }

  function collectItems() {
    const rows = Array.from(items.querySelectorAll("tr"));
    return rows
      .map((row) => ({
        item_code: row.querySelector(".item-code").value.trim(),
        item_description: row.querySelector(".item-desc").value.trim(),
        width: row.querySelector(".item-width").value,
        length: row.querySelector(".item-length").value,
        qty: row.querySelector(".item-qty").value,
      }))
      .filter((row) => row.item_code);
  }

  async function saveDraft() {
    const payload = {
      client_code: qs("client-code").value.trim(),
      client_name: qs("client-name").value.trim(),
      required_date: qs("required-date").value,
      local_export: qs("local-export").value,
      remark: qs("remark").value.trim(),
      client_po_list: collectList(poList),
      do_to_supplier_list: collectList(supplierList),
      items: collectItems(),
    };

    const res = await api.post("/api/orders", payload);
    if (!res.ok) {
      resultBox.textContent = res.error || "Failed to create order";
      return null;
    }
    currentJo = res.data.jo_number;
    resultBox.textContent = `Draft saved. JO number: ${currentJo}`;
    return currentJo;
  }

  qs("save-draft").addEventListener("click", async () => {
    await saveDraft();
  });

  qs("confirm-order").addEventListener("click", async () => {
    const jo = currentJo || (await saveDraft());
    if (!jo) return;
    const res = await api.post(`/api/orders/${jo}/confirm`);
    if (!res.ok) {
      resultBox.textContent = res.error || "Confirm failed";
      return;
    }
    const doNumber = res.data.do_client_number;
    resultBox.textContent = `Confirmed. DO number: ${doNumber}`;
    window.location.href = `/delivery/${doNumber}`;
  });

  qs("client-code").addEventListener("blur", loadClientSnapshot);
  qs("client-code").addEventListener("change", loadClientSnapshot);
}

async function initDashboard() {
  const yearInput = qs("filter-year");
  const monthInput = qs("filter-month");
  const statusInput = qs("filter-status");
  const rowsEl = qs("order-rows");
  const countEl = qs("order-count");

  const today = new Date();
  yearInput.value = today.getFullYear();
  monthInput.value = today.getMonth() + 1;

  async function load() {
    const url = new URL("/api/orders", window.location.origin);
    url.searchParams.set("year", yearInput.value);
    url.searchParams.set("month", monthInput.value);
    if (statusInput.value) {
      url.searchParams.set("status", statusInput.value);
    }

    const res = await api.get(url.toString());
    rowsEl.innerHTML = "";
    res.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.issue_date || ""}</td>
        <td>${row.jo_number || ""}</td>
        <td>${row.client_po_list || ""}</td>
        <td>${row.client_name || ""}</td>
        <td>${row.required_date || ""}</td>
        <td>${row.do_to_supplier_first || ""}</td>
        <td>${row.do_client_number || ""}</td>
        <td>${row.status || ""}</td>
        <td>${row.complete_date || ""}</td>
        <td class="actions-cell"></td>
      `;
      const actionsCell = tr.querySelector(".actions-cell");
      if (row.status === "Preparing" && !row.do_client_number) {
        const btn = document.createElement("button");
        btn.className = "btn btn--ghost";
        btn.textContent = "Confirm";
        btn.addEventListener("click", async () => {
          const confirmRes = await api.post(`/api/orders/${row.jo_number}/confirm`);
          if (confirmRes.ok) {
            load();
          } else {
            alert(confirmRes.error || "Confirm failed");
          }
        });
        actionsCell.appendChild(btn);
      }
      if (row.status === "Delivering") {
        const btn = document.createElement("button");
        btn.className = "btn btn--ghost";
        btn.textContent = "Complete";
        btn.addEventListener("click", async () => {
          const completeRes = await api.post(
            `/api/orders/${row.jo_number}/complete`
          );
          if (completeRes.ok) {
            load();
          } else {
            alert(completeRes.error || "Complete failed");
          }
        });
        actionsCell.appendChild(btn);
      }
      if (row.status === "Preparing" || row.status === "Delivering") {
        const btn = document.createElement("button");
        btn.className = "btn btn--ghost";
        btn.textContent = "Cancel";
        btn.addEventListener("click", async () => {
          const cancelRes = await api.post(
            `/api/orders/${row.jo_number}/cancel`
          );
          if (cancelRes.ok) {
            load();
          } else {
            alert(cancelRes.error || "Cancel failed");
          }
        });
        actionsCell.appendChild(btn);
      }
      if (row.do_client_number) {
        const link = document.createElement("a");
        link.className = "btn btn--ghost";
        link.textContent = "Open DO";
        link.href = `/delivery/${row.do_client_number}`;
        actionsCell.appendChild(link);
      }
      rowsEl.appendChild(tr);
    });
    countEl.textContent = res.length;
  }

  qs("apply-filter").addEventListener("click", load);
  load();
}

async function initDeliveryOrder() {
  const doNumber = window.DO_NUMBER;
  const titleEl = qs("do-title");
  const infoEl = qs("client-info");
  const itemsEl = qs("do-items");
  const remarkEl = qs("do-remark");

  const res = await api.get(`/api/delivery/${doNumber}`);
  if (!res.ok) {
    titleEl.textContent = "Delivery Order";
    remarkEl.textContent = res.error || "Failed to load delivery order";
    return;
  }
  const data = res.data;
  titleEl.textContent = data.do_client_number || "Delivery Order";

  infoEl.innerHTML = `
    <div><strong>Client Code</strong><div class="muted">${data.client_code}</div></div>
    <div><strong>Client Name</strong><div class="muted">${data.client_name}</div></div>
    <div><strong>Delivery Address</strong><div class="muted">${data.delivery_address}</div></div>
    <div><strong>Client PIC</strong><div class="muted">${data.client_pic}</div></div>
    <div><strong>Contact</strong><div class="muted">${data.client_contact}</div></div>
    <div><strong>Client PO</strong><div class="muted">${data.client_po_list.join(", ")}</div></div>
  `;

  itemsEl.innerHTML = "";
  data.items.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.item_code || ""}</td>
      <td>${item.item_description || ""}</td>
      <td>${item.width || ""}</td>
      <td>${item.length || ""}</td>
      <td>${item.qty || ""}</td>
    `;
    itemsEl.appendChild(tr);
  });

  remarkEl.textContent = data.remark || "-";
}

if (page === "create-order") {
  initCreateOrder();
}
if (page === "dashboard") {
  initDashboard();
}
if (page === "delivery-order") {
  initDeliveryOrder();
}
