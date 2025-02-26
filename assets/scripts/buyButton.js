// Функция для покупки предмета
function setupBuyButtons() {
    document.querySelectorAll('.buy-button').forEach(button => {
        button.addEventListener('click', function () {
            const row = this.closest('tr');
            const itemName = row.querySelector('td:nth-child(1)').textContent.trim(); // Убедимся, что лишние пробелы удалены
            const itemGenerationPerHour = parseInt(row.querySelector('td:nth-child(2)').textContent, 10);
            const itemCost = parseInt(row.querySelector('.buy-button span').textContent, 10);

            const currencyAmount = document.getElementById('currency-amount');
            let currentBalance = parseInt(currencyAmount.textContent, 10);

            // Проверка, есть ли уже такой предмет в инвентаре
            const inventoryTable = document.querySelector('.inventory-table');
            let itemAlreadyExists = false;

            for (let i = 1; i < inventoryTable.rows.length; i++) {
                const existingItemName = inventoryTable.rows[i].cells[0].textContent.trim();
                if (existingItemName === itemName) {
                    itemAlreadyExists = true;
                    break;
                }
            }

            if (itemAlreadyExists) {
                alert('Этот предмет уже куплен!');
                return; // Прекращаем выполнение функции, если предмет уже есть
            }

            if (currentBalance >= itemCost) {
                currentBalance -= itemCost;
                currencyAmount.textContent = currentBalance;

                const newRow = inventoryTable.insertRow(-1);

                const cell1 = newRow.insertCell(0);
                const cell2 = newRow.insertCell(1);
                const cell3 = newRow.insertCell(2);

                cell1.textContent = itemName;
                cell2.textContent = itemGenerationPerHour;
                cell3.textContent = 'думаем';

                updateTotalGeneration();
            } else {
                alert('Недостаточно средств для покупки!');
            }

            this.blur();
        });
    });
}