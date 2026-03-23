const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const infoSection = document.getElementById("infoSection");
const imagesSection = document.getElementById("imagesSection");
const actionsSection = document.getElementById("actionsSection");
const messageDiv = document.getElementById("message");

// Drag and drop
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFile(e.target.files[0]);
  }
});

function showMessage(message, type = "info") {
  messageDiv.textContent = message;
  messageDiv.className = `message show ${type}`;

  setTimeout(() => {
    messageDiv.classList.remove("show");
  }, 4000);
}

function handleFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  showMessage("🔄 Processando arquivo...", "info");

  fetch("/api/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        displayInfo(data.data);
        generateImages(data.data);
        showMessage("✅ Arquivo processado com sucesso!", "success");
      } else {
        showMessage("❌ Erro: " + data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Erro:", error);
      showMessage("❌ Erro ao processar arquivo", "error");
    });
}

function displayInfo(data) {
  document.getElementById("packageId").textContent = data.package_id || "-";
  document.getElementById("trackingNumber").textContent =
    data.tracking_number || "-";
  document.getElementById("sender").textContent = data.sender || "-";
  document.getElementById("receiver").textContent = data.receiver || "-";
  document.getElementById("destination").textContent = data.destination || "-";
  document.getElementById("cep").textContent = data.cep || "-";

  infoSection.style.display = "block";
  actionsSection.style.display = "block";
}

function generateImages(data) {
  // Gerar QR Code
  if (data.qr_data || data.tracking_number) {
    const qrData = data.qr_data || data.tracking_number;
    document.getElementById("qrImage").src =
      `/api/generate-qr/${encodeURIComponent(qrData)}`;
  }

  // Gerar Código de Barras
  if (data.tracking_number) {
    document.getElementById("barcodeImage").src =
      `/api/generate-barcode/${encodeURIComponent(data.tracking_number)}`;
  }

  imagesSection.style.display = "block";
}

function downloadImage(type) {
  const imageElement =
    type === "qr"
      ? document.getElementById("qrImage")
      : document.getElementById("barcodeImage");
  const imageSrc = imageElement.src;

  const link = document.createElement("a");
  link.href = imageSrc;
  link.download = type === "qr" ? "qr-code.png" : "codigo-barras.png";
  link.click();

  showMessage(
    `✅ ${type === "qr" ? "QR Code" : "Código de Barras"} baixado!`,
    "success",
  );
}

function resetForm() {
  fileInput.value = "";
  infoSection.style.display = "none";
  imagesSection.style.display = "none";
  actionsSection.style.display = "none";
  document.getElementById("qrImage").src = "";
  document.getElementById("barcodeImage").src = "";
  showMessage("🔄 Pronto para processar outro arquivo", "info");
}
