  function scrollCarousel(direction) {
    const carousel = document.querySelector('.carousel-container');
    const scrollAmount = 300; // Défilement de 300px à chaque clic (ajustez si nécessaire)
    carousel.scrollBy({
      left: direction * scrollAmount,
      behavior: 'smooth'
    });
  }
