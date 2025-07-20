document.addEventListener("DOMContentLoaded", function () {
  console.log("scripts.js loaded");

  const carouselInner = document.getElementById("carouselInner");
  const carouselSlide = document.getElementById("carouselSlide");

  let currentIndex = 0;
  const mediaItems = Array.from(carouselInner.children);
  const visibleItems = Math.floor(carouselSlide.offsetWidth / 150);

  function updateCarousel() {
    const itemWidth = 150 + 10;
    carouselInner.style.transform = `translateX(-${currentIndex * itemWidth}px)`;
  }

  window.carouselNext = function () {
    if (currentIndex < mediaItems.length - visibleItems) {
      currentIndex++;
      updateCarousel();
    }
  };

  window.carouselPrev = function () {
    if (currentIndex > 0) {
      currentIndex--;
      updateCarousel();
    }
  };

  const modal = document.getElementById("mediaModal");
  const modalContent = document.getElementById("modalContent");
  let currentModalIndex = 0;

  window.openMediaModal = function (type, url) {
    modal.style.display = "block";
    currentModalIndex = mediaItems.findIndex((item) => {
      const img = item.querySelector("img");
      return img && (img.src.includes(url) || img.src.includes(url.split('/').pop()));
    });
    showMedia(currentModalIndex);
  };

  window.closeMediaModal = function () {
    modal.style.display = "none";
    modalContent.innerHTML = "";
  };

  window.showNextMedia = function () {
    if (currentModalIndex < mediaItems.length - 1) {
      currentModalIndex++;
      showMedia(currentModalIndex);
    }
  };

  window.showPrevMedia = function () {
    if (currentModalIndex > 0) {
      currentModalIndex--;
      showMedia(currentModalIndex);
    }
  };

  function showMedia(index) {
    const item = mediaItems[index];
    const img = item.querySelector("img");
    modalContent.innerHTML = "";

    // Detects YouTube thumbnails and embeds video
    if (img.src.includes("youtube.com") || img.src.includes("ytimg.com")) {
      const videoId = img.src.split("/vi/")[1]?.split("/")[0];
      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
      iframe.style.width = "100%";
      iframe.style.height = "540px";
      iframe.frameBorder = "0";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      modalContent.appendChild(iframe);
    } else {
      const largeImg = document.createElement("img");
      largeImg.src = img.src;
      largeImg.alt = "Media";
      largeImg.style.maxWidth = "100%";
      largeImg.style.maxHeight = "90vh";
      largeImg.style.borderRadius = "8px";
      modalContent.appendChild(largeImg);
    }
  }

  document.addEventListener("keydown", function (e) {
    if (modal.style.display === "block") {
      if (e.key === "ArrowRight") showNextMedia();
      if (e.key === "ArrowLeft") showPrevMedia();
      if (e.key === "Escape") closeMediaModal();
    }
  });
});
