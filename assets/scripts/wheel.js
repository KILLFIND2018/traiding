/*колесо фортуны*/
const spinButton = document.getElementById('spin-button');
const wheel = document.getElementById('wheel');
const currencyAmount = document.getElementById('currency-amount');
let spinning = false;

spinButton.addEventListener('click', () => {
    if (spinning) return;

    const currentBalance = parseInt(currencyAmount.textContent, 10);
    const spinCost = 34;

    if (currentBalance < spinCost) {
        alert('Недостаточно монет для вращения колеса!');
        return;
    }

    spinning = true;

    // Вычитаем стоимость вращения из баланса
    currencyAmount.textContent = currentBalance - spinCost;

    const degrees = Math.floor(Math.random() * 360) + 1440;
    wheel.style.transform = `rotate(${degrees}deg)`;
    wheel.style.transition = 'transform 5s ease-out';

    setTimeout(() => {
        spinning = false;
        const actualDegrees = degrees % 360;
        const segmentDegree = 360 / 6;
        const winningSegment = Math.floor(actualDegrees / segmentDegree);
        console.log(`Вы выиграли приз: ${winningSegment + 1}`);
    }, 5000);
});