let images = [];
let index = 0;
let timer;

function startSlideshow(folder, interval = 5000) {
  fetch(`/list/${folder}`)
    .then((res) => res.json())
    .then((data) => {
      images = data;
      index = 0;
      if (timer) clearInterval(timer);
      if (images.length > 0) {
        showImage(images[0]);
        timer = setInterval(nextImage, interval); // dynamisch!
      }
    });
}

function nextImage() {
  index = (index + 1) % images.length;
  showImage(images[index]);
}

function showImage(src) {
  const img = document.getElementById("slideshow");
  img.style.opacity = 0;
  setTimeout(() => {
    img.src = src;
    img.onload = () => {
      img.style.opacity = 1;
    };
  }, 500); // Zeit fürs Ausblenden
}
