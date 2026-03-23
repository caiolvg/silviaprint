const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const infoSection = document.getElementById("infoSection");
const previewSection = document.getElementById("previewSection");
const imagesSection = document.getElementById("imagesSection");
const actionsSection = document.getElementById("actionsSection");
const messageDiv = document.getElementById("message");

// Variável global para armazenar os dados da etiqueta
let currentLabelData = null;

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

  showMessage("Processando arquivo...", "info");

  fetch("/api/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        displayInfo(data.data);
        generateImages(data.data);
        showMessage("Arquivo processado com sucesso!", "success");
      } else {
        showMessage("Erro: " + data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Erro:", error);
      showMessage("Erro ao processar arquivo", "error");
    });
}

function displayInfo(data) {
  currentLabelData = data;
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
      `https://quickchart.io/qr?text=${encodeURIComponent(qrData)}&size=260`;
  }

  // Gerar Código de Barras
  if (data.tracking_number) {
    document.getElementById("barcodeImage").src =
      `https://bwipjs-api.metafloor.com/?bcid=code128&scale=3&includetext=true&text=${encodeURIComponent(data.tracking_number)}`;
  }

  // Gerar Preview da Etiqueta Completa
  generateLabelPreview(data);

  imagesSection.style.display = "block";
}

function generateLabelPreview(data) {
  fetch("/api/generate-label-preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
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
      document.getElementById("previewImage").src = url;
      previewSection.style.display = "block";
    })
    .catch((error) => {
      console.error("Erro ao gerar preview:", error);
      previewSection.style.display = "none";
      showMessage(
        error.message || "Erro ao gerar visualização da etiqueta",
        "error",
      );
    });
}

function downloadImage(type) {
  let imageElement;
  let filename;

  if (type === "qr") {
    imageElement = document.getElementById("qrImage");
    filename = "qr-code.png";
  } else if (type === "barcode") {
    imageElement = document.getElementById("barcodeImage");
    filename = "codigo-barras.png";
  } else if (type === "preview") {
    imageElement = document.getElementById("previewImage");
    filename = "etiqueta-completa.png";
  }

  if (!imageElement || !imageElement.src) {
    showMessage("Imagem não disponível", "error");
    return;
  }

  const imageSrc = imageElement.src;

  const link = document.createElement("a");
  link.href = imageSrc;
  link.download = filename;
  link.click();

  showMessage(`${filename.replace(".png", "")} baixado!`, "success");
}

function resetForm() {
  fileInput.value = "";
  currentLabelData = null;
  infoSection.style.display = "none";
  previewSection.style.display = "none";
  imagesSection.style.display = "none";
  actionsSection.style.display = "none";
  document.getElementById("qrImage").src = "";
  document.getElementById("barcodeImage").src = "";
  document.getElementById("previewImage").src = "";
  showMessage("Pronto para processar outro arquivo", "info");
}
