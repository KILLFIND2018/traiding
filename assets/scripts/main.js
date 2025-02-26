
// Базовая генерация: 1 монета в 1 секунду
const BASE_GENERATION = 1;



// Функция для обновления общей генерации и отображение моделей
function updateTotalGeneration() {
    const inventoryTable = document.querySelector('.inventory-table');
    let totalGeneration = BASE_GENERATION;

    hasOlderPC = false;
    hasSpeaker = false;
    hasServer = false;
    hasCafetalg = false;
    hasPanasonic = false;
    hasScifiSciderRobot = false;
    hasTheGlobe = false;

    for (let i = 1; i < inventoryTable.rows.length; i++) {
        let itemName = inventoryTable.rows[i].cells[0].innerText;
        let generationPerHour = parseInt(inventoryTable.rows[i].cells[1].innerText, 10);

        if (!isNaN(generationPerHour)) {
            const generationPer5Seconds = generationPerHour;
            totalGeneration += generationPer5Seconds;
        }

        if (itemName.trim() === "Older PC") {
            hasOlderPC = true;
        } else if (itemName.trim() === "Speaker") {
            hasSpeaker = true;
        } else if (itemName.trim() === "Server") {
            hasServer = true;
        } else if (itemName.trim() === "Cafetalg") {
            hasCafetalg = true;
        } else if (itemName.trim() === "Panasonic") {
            hasPanasonic = true;
        } else if (itemName.trim() === "Scifi Scider Robot") {
            hasScifiSciderRobot = true;
        } else if (itemName.trim() === "The Globe") {
            hasTheGlobe = true;
        }
    }

    if (hasOlderPC) {
        olderPC();
    }
    if (hasSpeaker) {
        speaker();
    }
    if (hasServer) {
        server();
    }
    if (hasCafetalg) {
        cafetalg();
    }
    if (hasPanasonic) {
        panasonic();
    }
    if (hasScifiSciderRobot) {
        scifisciderrobot();
    }
    if (hasTheGlobe) {
        theglobe();
    }

    increaseBalance(totalGeneration);
}

// Переменная для хранения интервала генерации баланса
let balanceInterval;

// Функция для увеличения баланса
function increaseBalance(totalGeneration) {
    const currencyAmount = document.getElementById('currency-amount');

    if (balanceInterval) {
        clearInterval(balanceInterval);
    }

    balanceInterval = setInterval(() => {
        let currentBalance = parseInt(currencyAmount.textContent, 10);
        currentBalance += totalGeneration;
        currencyAmount.textContent = Math.floor(currentBalance);
    }, 1000);
}

