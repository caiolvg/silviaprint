const MAX_FILES = 100;

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const clearButton = document.getElementById("clearButton");
const batchStatus = document.getElementById("batchStatus");
const totalCount = document.getElementById("totalCount");
const successCount = document.getElementById("successCount");
const errorCount = document.getElementById("errorCount");
const queuePanel = document.getElementById("queuePanel");
const detailPanel = document.getElementById("detailPanel");
const fileList = document.getElementById("fileList");
const searchInput = document.getElementById("searchInput");
const messageDiv = document.getElementById("message");

const selectedFilename = document.getElementById("selectedFilename");
const previewButton = document.getElementById("previewButton");
const previewImage = document.getElementById("previewImage");
const previewPlaceholder = document.getElementById("previewPlaceholder");
const qrImage = document.getElementById("qrImage");
const barcodeImage = document.getElementById("barcodeImage");
const downloadPreviewButton = document.getElementById("downloadPreviewButton");
const downloadQrButton = document.getElementById("downloadQrButton");
const downloadBarcodeButton = document.getElementById("downloadBarcodeButton");

const appState = {
  results: [],
  selectedIndex: null,
  previewUrls: new Map(),
};

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", (event) => {
  if (!dropZone.contains(event.relatedTarget)) {
    dropZone.classList.remove("dragover");
  }
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
  handleFiles(event.dataTransfer.files);
});

fileInput.addEventListener("change", (event) => {
  handleFiles(event.target.files);
});

clearButton.addEventListener("click", resetWorkspace);
searchInput.addEventListener("input", renderFileList);
previewButton.addEventListener("click", generateSelectedPreview);
downloadPreviewButton.addEventListener("click", () => downloadImage("preview"));
downloadQrButton.addEventListener("click", () => downloadImage("qr"));
downloadBarcodeButton.addEventListener("click", () => downloadImage("barcode"));

function showMessage(message, type = "info") {
  messageDiv.textContent = message;
  messageDiv.className = `message show ${type}`;

  setTimeout(() => {
    messageDiv.classList.remove("show");
  }, 4500);
}

function handleFiles(fileListObject) {
  const files = Array.from(fileListObject || []);

  if (!files.length) {
    return;
  }

  if (files.length > MAX_FILES) {
    showMessage(`Envie no maximo ${MAX_FILES} arquivos por lote.`, "error");
    fileInput.value = "";
    return;
  }

  uploadBatch(files);
}

function uploadBatch(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  setLoading(true);
  showMessage("Processando lote...", "info");

  fetch("/api/upload-batch", {
    method: "POST",
    body: formData,
  })
    .then(async (response) => {
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(payload?.error || "Falha ao processar arquivos");
      }
      return payload;
    })
    .then((payload) => {
      appState.results = payload.results || [];
      appState.selectedIndex = findFirstSuccessfulIndex(appState.results);
      updateSummary(payload.summary);
      renderFileList();
      renderSelectedLabel();

      const ok = payload.summary?.success || 0;
      const errors = payload.summary?.errors || 0;
      const suffix = errors ? `, ${errors} com erro` : "";
      showMessage(`${ok} arquivo(s) processado(s)${suffix}.`, ok ? "success" : "error");
    })
    .catch((error) => {
      console.error("Erro:", error);
      showMessage(error.message || "Erro ao processar arquivos", "error");
    })
    .finally(() => {
      setLoading(false);
      fileInput.value = "";
    });
}

function findFirstSuccessfulIndex(results) {
  const index = results.findIndex((result) => result.success);
  return index >= 0 ? index : null;
}

function updateSummary(summary = {}) {
  totalCount.textContent = summary.total ?? appState.results.length;
  successCount.textContent = summary.success ?? countByStatus(true);
  errorCount.textContent = summary.errors ?? countByStatus(false);
  batchStatus.hidden = false;
  queuePanel.hidden = appState.results.length === 0;
}

function countByStatus(status) {
  return appState.results.filter((result) => result.success === status).length;
}

function renderFileList() {
  const query = normalize(searchInput.value);
  const filtered = appState.results
    .map((result, index) => ({ result, index }))
    .filter(({ result }) => matchesSearch(result, query));

  fileList.innerHTML = "";

  if (!filtered.length) {
    const emptyState = document.createElement("p");
    emptyState.className = "empty-state";
    emptyState.textContent = "Nenhum arquivo encontrado.";
    fileList.appendChild(emptyState);
    return;
  }

  filtered.forEach(({ result, index }) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `file-row ${result.success ? "is-success" : "is-error"}`;
    if (index === appState.selectedIndex) {
      item.classList.add("is-active");
    }

    item.innerHTML = `
      <span class="file-status">${result.success ? "OK" : "ERRO"}</span>
      <span class="file-main">
        <strong>${escapeHtml(result.filename)}</strong>
        <small>${escapeHtml(getResultSubtitle(result))}</small>
      </span>
    `;

    item.addEventListener("click", () => {
      appState.selectedIndex = index;
      renderFileList();
      renderSelectedLabel();
    });

    fileList.appendChild(item);
  });
}

function matchesSearch(result, query) {
  if (!query) {
    return true;
  }

  const data = result.data || {};
  return [
    result.filename,
    data.tracking_number,
    data.package_id,
    data.receiver,
    data.destination,
    result.error,
  ].some((value) => normalize(value).includes(query));
}

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function getResultSubtitle(result) {
  if (!result.success) {
    return result.error || "Nao processado";
  }

  const data = result.data || {};
  return [data.tracking_number, data.receiver, data.destination]
    .filter(Boolean)
    .join(" - ") || "Etiqueta lida sem dados principais";
}

function renderSelectedLabel() {
  const selected = appState.results[appState.selectedIndex];
  detailPanel.hidden = !selected;

  if (!selected) {
    return;
  }

  selectedFilename.textContent = selected.filename;

  if (!selected.success) {
    setInfoValues({});
    clearMedia();
    previewButton.disabled = true;
    showMessage(selected.error || "Arquivo com erro", "error");
    return;
  }

  const data = selected.data || {};
  previewButton.disabled = false;
  setInfoValues(data);
  renderGeneratedAssets(data);
  renderCachedPreview();
}

function setInfoValues(data) {
  document.getElementById("packageId").textContent = data.package_id || "-";
  document.getElementById("trackingNumber").textContent = data.tracking_number || "-";
  document.getElementById("sender").textContent = data.sender || "-";
  document.getElementById("receiver").textContent = data.receiver || "-";
  document.getElementById("destination").textContent = data.destination || "-";
  document.getElementById("cep").textContent = data.cep || "-";
}

function renderGeneratedAssets(data) {
  const qrData = data.qr_data || data.tracking_number;
  qrImage.src = qrData
    ? `https://quickchart.io/qr?text=${encodeURIComponent(qrData)}&size=260`
    : "";

  barcodeImage.src = data.tracking_number
    ? `https://bwipjs-api.metafloor.com/?bcid=code128&scale=3&includetext=true&text=${encodeURIComponent(data.tracking_number)}`
    : "";
}

function renderCachedPreview() {
  const cachedUrl = appState.previewUrls.get(appState.selectedIndex);
  previewImage.src = cachedUrl || "";
  previewImage.hidden = !cachedUrl;
  previewPlaceholder.hidden = Boolean(cachedUrl);
}

function clearMedia() {
  qrImage.src = "";
  barcodeImage.src = "";
  previewImage.src = "";
  previewImage.hidden = true;
  previewPlaceholder.hidden = false;
}

function generateSelectedPreview() {
  const selected = appState.results[appState.selectedIndex];
  if (!selected?.success) {
    showMessage("Selecione uma etiqueta valida.", "error");
    return;
  }

  const cachedUrl = appState.previewUrls.get(appState.selectedIndex);
  if (cachedUrl) {
    renderCachedPreview();
    return;
  }

  previewButton.disabled = true;
  previewButton.textContent = "Gerando...";

  fetch("/api/generate-label-preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(selected.data),
  })
    .then(async (response) => {
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.error || "Falha ao gerar preview da etiqueta");
      }
      return response.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      appState.previewUrls.set(appState.selectedIndex, url);
      renderCachedPreview();
      showMessage("Preview gerado.", "success");
    })
    .catch((error) => {
      console.error("Erro ao gerar preview:", error);
      showMessage(error.message || "Erro ao gerar visualizacao da etiqueta", "error");
    })
    .finally(() => {
      previewButton.disabled = false;
      previewButton.textContent = "Gerar preview";
    });
}

function downloadImage(type) {
  const imageMap = {
    preview: { element: previewImage, filename: "etiqueta-completa.png" },
    qr: { element: qrImage, filename: "qr-code.png" },
    barcode: { element: barcodeImage, filename: "codigo-barras.png" },
  };
  const target = imageMap[type];

  if (!target?.element?.src) {
    showMessage("Imagem nao disponivel.", "error");
    return;
  }

  const link = document.createElement("a");
  link.href = target.element.src;
  link.download = target.filename;
  link.click();
}

function setLoading(isLoading) {
  dropZone.classList.toggle("loading", isLoading);
  dropZone.setAttribute("aria-busy", String(isLoading));
}

function resetWorkspace() {
  appState.previewUrls.forEach((url) => URL.revokeObjectURL(url));
  appState.previewUrls.clear();
  appState.results = [];
  appState.selectedIndex = null;
  fileInput.value = "";
  searchInput.value = "";
  fileList.innerHTML = "";
  batchStatus.hidden = true;
  queuePanel.hidden = true;
  detailPanel.hidden = true;
  clearMedia();
  showMessage("Fila limpa.", "info");
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
