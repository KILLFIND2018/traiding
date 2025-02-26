/*смена двух блоков колеса и магазина*/
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', (event) => {
    touchStartX = event.touches[0].clientX;
});

document.addEventListener('touchend', (event) => {
    touchEndX = event.changedTouches[0].clientX;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50; // Минимальная длина свайпа для срабатывания
    const swipeDistance = touchEndX - touchStartX;

    if (Math.abs(swipeDistance) < swipeThreshold) return; // Игнорируем короткие свайпы

    const martContainer = document.querySelector('.mart-container');
    const wheelContainer = document.querySelector('.wheel-container');

    if (swipeDistance < 0) {
        // Свайп вправо
        fadeOut(wheelContainer);
        fadeIn(martContainer);
    } else {
        // Свайп влево
        fadeOut(martContainer);
        fadeIn(wheelContainer);
    }
}

function fadeOut(element) {
    element.style.transition = 'opacity 0.5s';
    element.style.opacity = '0';
    element.addEventListener('transitionend', () => {
        element.style.display = 'none';
    }, { once: true });
}

function fadeIn(element) {
    element.style.opacity = '0';
    element.style.display = 'block';
    element.style.transition = 'opacity 0.5s';
    // Используем setTimeout для того, чтобы браузер успел применить display: block перед изменением opacity
    setTimeout(() => {
        element.style.opacity = '1';
    }, 10);
}