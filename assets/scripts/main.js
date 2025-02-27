// Базовая генерация: 1 монета в 1 секунду
const BASE_GENERATION = 1;

// Коэффициент геометрической прогрессии
const PROGRESSION_RATE = 1.01; // 1% увеличение каждые 10 секунд

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
    hasDrinkingWaterDispenser = false;
    hasHumanoidRobot = false;

    for (let i = 1; i < inventoryTable.rows.length; i++) {
        let itemName = inventoryTable.rows[i].cells[0].innerText;
        let generationPerHour = parseInt(inventoryTable.rows[i].cells[1].innerText, 10);

        if (!isNaN(generationPerHour)) {
            const generationPerSecond = generationPerHour; //секунды
            totalGeneration += generationPerSecond;
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
        } else if (itemName.trim() === "Drinking Water Dispenser") {
            hasDrinkingWaterDispenser = true;
        } else if (itemName.trim() === "Humanoid robot") {
            hasHumanoidRobot = true;
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
    if (hasDrinkingWaterDispenser) {
        drinkingWaterDispenser();
    }
    if (hasHumanoidRobot) {
        humanoidRobot();
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

    let progressionFactor = 1;

    // Увеличиваем баланс каждую секунду, но прогрессию — каждые 10 секунд
    balanceInterval = setInterval(() => {
        let currentBalance = parseInt(currencyAmount.textContent, 10);
        currentBalance += totalGeneration * progressionFactor;
        currencyAmount.textContent = Math.floor(currentBalance);
    }, 1000); // Обновление баланса каждую секунду

    // Отдельный интервал для увеличения коэффициента прогрессии каждые 10 секунд
    setInterval(() => {
        progressionFactor *= PROGRESSION_RATE;
        console.log(`Прогрессия увеличена раз в 10 сек. Новый коэффициент: ${progressionFactor.toFixed(2)}`);
    }, 10000); // Увеличение прогрессии каждые 10 секунд
}

// Функция для добавления бонусного предмета "Older PC"
function addBonusOlderPC() {
    const inventoryTable = document.querySelector('.inventory-table');
    const newRow = inventoryTable.insertRow(-1);

    const cell1 = newRow.insertCell(0);
    const cell2 = newRow.insertCell(1);
    const cell3 = newRow.insertCell(2);

    cell1.textContent = 'Older PC';
    cell2.textContent = 10; // Например, генерация 10 единиц в секунду
    cell3.textContent = 'думаем';
}

// Инициализация общей генерации при загрузке страницы
function initializeTotalGeneration() {
    const table = document.querySelector('.inventory-table');
    let totalGeneration = BASE_GENERATION;

    // Проверяем, есть ли уже бонусный предмет "Older PC"
    let hasBonusOlderPC = false;
    for (let i = 1; i < table.rows.length; i++) {
        if (table.rows[i].cells[0].textContent === 'Older PC') {
            hasBonusOlderPC = true;
            break;
        }
    }

    // Если бонусный предмет отсутствует, добавляем его
    if (!hasBonusOlderPC) {
        addBonusOlderPC();
    }

    // Пересчитываем общую генерацию
    for (let i = 1; i < table.rows.length; i++) {
        let generationPerHour = parseInt(table.rows[i].cells[1].innerText, 10);

        if (!isNaN(generationPerHour)) {
            const generationPerSecond = generationPerHour; // секунды
            totalGeneration += generationPerSecond;
        }
    }
    updateTotalGeneration();
    increaseBalance(totalGeneration);
}

// Вызов функции инициализации при загрузке страницы
initializeTotalGeneration();