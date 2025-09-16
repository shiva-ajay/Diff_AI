// P&ID Diff Finder JavaScript

class DiffFinder {
  constructor() {
    this.referenceFile = null;
    this.compareFile = null;
    this.apiBaseUrl = window.location.origin; // Use current origin instead of hardcoded localhost
    this.currentZoom = 1;
    this.currentImageType = null;
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.imagePosition = { x: 0, y: 0 };

    this.initializeEventListeners();
  }

  initializeEventListeners() {
    console.log("Initializing event listeners...");

    // File input handlers
    const referenceInput = document.getElementById("referenceFile");
    const compareInput = document.getElementById("compareFile");
    const findBtn = document.getElementById("findDifferencesBtn");

    if (referenceInput) {
      referenceInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.handleFile(e.target.files[0], "reference");
        }
      });
    }

    if (compareInput) {
      compareInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.handleFile(e.target.files[0], "compare");
        }
      });
    }

    if (findBtn) {
      findBtn.addEventListener("click", () => this.findDifferences());
    }

    // Drag and drop handlers
    this.setupDragAndDrop("referenceUpload", "referenceFile", "reference");
    this.setupDragAndDrop("compareUpload", "compareFile", "compare");
  }

  setupDragAndDrop(uploadAreaId, inputId, type) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(inputId);

    if (!uploadArea || !fileInput) return;

    uploadArea.addEventListener("click", () => fileInput.click());

    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFile(files[0], type);
      }
    });
  }

  handleFile(file, type) {
    console.log(
      `Handling file: ${file.name}, type: ${type}, size: ${file.size}`
    );

    // Validate file type
    if (!file.type.startsWith("image/")) {
      this.showError("Please select a valid image file (JPEG, PNG)");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      this.showError("File size must be less than 10MB");
      return;
    }

    if (type === "reference") {
      this.referenceFile = file;
      this.showPreview(file, "reference");
    } else {
      this.compareFile = file;
      this.showPreview(file, "compare");
    }

    this.updateFindButton();
  }

  showPreview(file, type) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const uploadContent = document.querySelector(
        `#${type}Upload .upload-content`
      );
      const uploadPreview = document.querySelector(
        `#${type}Upload .upload-preview`
      );
      const img = document.getElementById(`${type}Img`);
      const nameSpan = document.getElementById(`${type}Name`);

      uploadContent.style.display = "none";
      uploadPreview.style.display = "block";
      img.src = e.target.result;
      nameSpan.textContent = file.name;
    };
    reader.readAsDataURL(file);
  }

  removeFile(type) {
    if (type === "reference") {
      this.referenceFile = null;
      document.getElementById("referenceFile").value = "";
    } else {
      this.compareFile = null;
      document.getElementById("compareFile").value = "";
    }

    const uploadContent = document.querySelector(
      `#${type}Upload .upload-content`
    );
    const uploadPreview = document.querySelector(
      `#${type}Upload .upload-preview`
    );

    uploadContent.style.display = "flex";
    uploadPreview.style.display = "none";

    this.updateFindButton();
  }

  updateFindButton() {
    const findBtn = document.getElementById("findDifferencesBtn");
    findBtn.disabled = !(this.referenceFile && this.compareFile);
  }

  async findDifferences() {
    if (!this.referenceFile || !this.compareFile) {
      this.showError("Please select both reference and compare images");
      return;
    }

    this.showProgress();

    try {
      const formData = new FormData();
      formData.append("reference_image", this.referenceFile);
      formData.append("compare_image", this.compareFile);

      const response = await fetch(`${this.apiBaseUrl}/compare-images`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process images");
      }

      const result = await response.json();
      this.displayResults(result);
    } catch (error) {
      console.error("Error:", error);
      this.showError(
        error.message || "Failed to process images. Please try again."
      );
    } finally {
      this.hideProgress();
    }
  }

  showProgress() {
    document.getElementById("progressSection").style.display = "block";
    document.getElementById("resultsSection").style.display = "none";

    let progress = 0;
    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");

    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 90) progress = 90;

      progressFill.style.width = progress + "%";

      if (progress < 30) {
        progressText.textContent = "Analyzing images...";
      } else if (progress < 60) {
        progressText.textContent = "Computing differences...";
      } else {
        progressText.textContent = "Generating visualizations...";
      }
    }, 200);

    // Store interval ID to clear it later
    this.progressInterval = interval;
  }

  hideProgress() {
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
    }

    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");

    progressFill.style.width = "100%";
    progressText.textContent = "Complete!";

    setTimeout(() => {
      document.getElementById("progressSection").style.display = "none";
    }, 500);
  }

  displayResults(result) {
    // Update similarity score
    const scoreValue = document.getElementById("scoreValue");
    const score = (result.similarity_score * 100).toFixed(1);
    scoreValue.textContent = `${score}%`;

    // Store results for download functionality
    const baseUrl = this.apiBaseUrl;
    this.results = {
      ssim: baseUrl + result.results.ssim_difference,
      bounded: baseUrl + result.results.bounded_differences,
      drawn: baseUrl + result.results.drawn_differences,
      mask: baseUrl + result.results.mask_differences,
    };

    // Update result images
    document.getElementById("ssimResult").src = this.results.ssim;
    document.getElementById("boundedResult").src = this.results.bounded;
    document.getElementById("drawnResult").src = this.results.drawn;
    document.getElementById("maskResult").src = this.results.mask;

    // Show results section
    document.getElementById("resultsSection").style.display = "block";

    // Scroll to results
    document.getElementById("resultsSection").scrollIntoView({
      behavior: "smooth",
    });
  }

  showError(message) {
    const toast = document.getElementById("errorToast");
    const errorMessage = document.getElementById("errorMessage");

    errorMessage.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
    }, 5000);
  }
}

// Modal functionality
function openModal(type) {
  const modal = document.getElementById("imageModal");
  const modalImage = document.getElementById("modalImage");
  const modalTitle = document.getElementById("modalTitle");
  const imageContainer = document.getElementById("imageContainer");

  const titles = {
    ssim: "SSIM Difference",
    bounded: "Bounded Differences",
    drawn: "Drawn Differences",
    mask: "Mask Differences",
  };

  const images = {
    ssim: document.getElementById("ssimResult"),
    bounded: document.getElementById("boundedResult"),
    drawn: document.getElementById("drawnResult"),
    mask: document.getElementById("maskResult"),
  };

  // Set current image type for download functionality
  diffFinder.currentImageType = type;

  // Reset zoom and position
  diffFinder.currentZoom = 1;
  diffFinder.imagePosition = { x: 0, y: 0 };

  modalTitle.textContent = titles[type];
  modalImage.src = images[type].src;

  // Reset image transform
  modalImage.style.transform = "translate(0px, 0px) scale(1)";

  modal.style.display = "block";

  // Setup pan functionality
  setupPanFunctionality(imageContainer, modalImage);

  // Prevent body scroll
  document.body.style.overflow = "hidden";
}

function closeModal() {
  const modal = document.getElementById("imageModal");
  modal.style.display = "none";

  // Clear current image type
  diffFinder.currentImageType = null;

  // Restore body scroll
  document.body.style.overflow = "auto";
}

// Pan functionality setup
function setupPanFunctionality(container, image) {
  // Remove existing listeners
  container.onmousedown = null;
  container.onwheel = null;

  // Mouse drag for panning
  container.onmousedown = function (e) {
    if (diffFinder.currentZoom <= 1) return; // Only allow panning when zoomed in

    diffFinder.isDragging = true;
    diffFinder.dragStart.x = e.clientX - diffFinder.imagePosition.x;
    diffFinder.dragStart.y = e.clientY - diffFinder.imagePosition.y;

    container.style.cursor = "grabbing";
    e.preventDefault();
  };

  document.onmousemove = function (e) {
    if (!diffFinder.isDragging) return;

    diffFinder.imagePosition.x = e.clientX - diffFinder.dragStart.x;
    diffFinder.imagePosition.y = e.clientY - diffFinder.dragStart.y;

    updateImageTransform();
    e.preventDefault();
  };

  document.onmouseup = function () {
    if (diffFinder.isDragging) {
      diffFinder.isDragging = false;
      container.style.cursor = diffFinder.currentZoom > 1 ? "grab" : "default";
    }
  };

  // Mouse wheel for zooming
  container.onwheel = function (e) {
    e.preventDefault();

    const rect = container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;

    const oldZoom = diffFinder.currentZoom;

    if (e.deltaY < 0) {
      diffFinder.currentZoom = Math.min(diffFinder.currentZoom * 1.1, 5);
    } else {
      diffFinder.currentZoom = Math.max(diffFinder.currentZoom / 1.1, 0.1);
    }

    // Adjust position to zoom towards mouse cursor
    const zoomRatio = diffFinder.currentZoom / oldZoom;
    diffFinder.imagePosition.x =
      mouseX - (mouseX - diffFinder.imagePosition.x) * zoomRatio;
    diffFinder.imagePosition.y =
      mouseY - (mouseY - diffFinder.imagePosition.y) * zoomRatio;

    // Update cursor based on zoom level
    container.style.cursor = diffFinder.currentZoom > 1 ? "grab" : "default";

    updateImageTransform();
  };
}

function removeFile(type) {
  diffFinder.removeFile(type);
}

// Zoom and Pan Functions
function zoomIn() {
  diffFinder.currentZoom = Math.min(diffFinder.currentZoom * 1.2, 5);
  updateImageTransform();
}

function zoomOut() {
  diffFinder.currentZoom = Math.max(diffFinder.currentZoom / 1.2, 0.1);
  updateImageTransform();
}

function resetZoom() {
  diffFinder.currentZoom = 1;
  diffFinder.imagePosition = { x: 0, y: 0 };
  updateImageTransform();
}

function updateImageTransform() {
  const modalImage = document.getElementById("modalImage");
  if (modalImage) {
    modalImage.style.transform = `translate(${diffFinder.imagePosition.x}px, ${diffFinder.imagePosition.y}px) scale(${diffFinder.currentZoom})`;
  }
}

// Download Functions
function downloadImage(imageType, filename) {
  if (!diffFinder.results || !diffFinder.results[imageType]) {
    showError("No image available for download");
    return;
  }

  const link = document.createElement("a");
  link.href = diffFinder.results[imageType];
  link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.jpg`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function downloadModalImage() {
  if (!diffFinder.currentImageType) {
    showError("No image available for download");
    return;
  }

  const typeNames = {
    ssim: "SSIM_Difference",
    bounded: "Bounded_Differences",
    drawn: "Drawn_Differences",
    mask: "Mask_Differences",
  };

  downloadImage(
    diffFinder.currentImageType,
    typeNames[diffFinder.currentImageType]
  );
}

// Initialize the application
const diffFinder = new DiffFinder();

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeModal();
  }
});

// Handle window resize for responsive behavior
window.addEventListener("resize", () => {
  // Any resize-specific logic can go here
});

console.log("P&ID Diff Finder initialized successfully");
