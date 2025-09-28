let images = [];
let preloaded = [];
let index = 0;
let timer;

// folder and interval are passed from template when starting
function startSlideshow(folder, interval = 5000) {
  fetch(`/list/${folder}`)
    .then((res) => res.json())
    .then((data) => {
      images = data;
      index = 0;
      preloaded = [];
      if (timer) clearInterval(timer);

      if (images.length === 0) return;

      // Preload all images
      let loadedCount = 0;
      images.forEach((src, i) => {
        const img = new Image();
        img.onload = () => {
          loadedCount++;
          // start as soon as first image is loaded to reduce wait
          if (loadedCount === 1) {
            showImage(preloaded[0] ? preloaded[0].src : src);
            timer = setInterval(nextImage, interval);
          }
        };
        img.onerror = () => {
          console.warn("Fehler beim Laden:", src);
        };
        img.src = src;
        preloaded[i] = img;
      });

      // Fallback: if none load within 5s, start anyway
      setTimeout(() => {
        if (!timer && images.length > 0) {
          showImage(preloaded[0] ? preloaded[0].src : images[0]);
          timer = setInterval(nextImage, interval);
        }
      }, 5000);
    });
}

function nextImage() {
  index = (index + 1) % images.length;
  const cached = preloaded[index];
  showImage(cached ? cached.src : images[index]);
}

function showImage(src) {
  const img = document.getElementById("slideshow");
  if (!img) return;
  img.style.opacity = 0;
  setTimeout(() => {
    img.src = src;
    img.onload = () => {
      img.style.opacity = 1;
    };
  }, 500);
}
