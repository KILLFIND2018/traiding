// Функция для добавления бонусного предмета "Older PC"
function addBonusOlderPC() {
    const inventoryTable = document.querySelector('.inventory-table');
    const newRow = inventoryTable.insertRow(-1);

    const cell1 = newRow.insertCell(0);
    const cell2 = newRow.insertCell(1);
    const cell3 = newRow.insertCell(2);

    cell1.textContent = 'Older PC';
    cell2.textContent = 10; // Например, генерация 10 единиц в час
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
            const generationPer5Seconds = generationPerHour;
            totalGeneration += generationPer5Seconds;
        }
    }
    updateTotalGeneration();
    increaseBalance(totalGeneration);
}

// Вызов функции инициализации при загрузке страницы
initializeTotalGeneration();