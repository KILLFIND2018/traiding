function formatNumber(num) {
    return Number(num).toLocaleString('ru-RU');
}

async function loadInventory(userId) {
    const response = await fetch(`/get_inventory?user_id=${userId}`);
    const data = await response.json();
    if (data.status === "success") {
        const inventoryTable = document.querySelector('.inventory-table');
        while (inventoryTable.rows.length > 1) {
            inventoryTable.deleteRow(1);
        }
        data.items.forEach(item => {
            const newRow = inventoryTable.insertRow(-1);
            newRow.classList.add('inventory-item');
            newRow.dataset.itemName = item.item_name;
            newRow.dataset.generation = item.generation_per_hour;
            newRow.insertCell(0).textContent = item.item_name;
            newRow.insertCell(1).textContent = formatNumber(item.generation_per_hour);
            newRow.insertCell(2).textContent = 'активен';
            updateTotalGeneration(item.item_name);
        });

        document.querySelectorAll('.inventory-item').forEach(row => {
            row.addEventListener('click', () => {
                const itemName = row.dataset.itemName;
                const generation = parseInt(row.dataset.generation) / 3600;
                const itemImage = `/static/img-market/${itemName.replace(/ /g, '_').toLowerCase()}.png`;

                document.getElementById('item-popup-name').textContent = itemName;
                document.getElementById('item-popup-profit').textContent = generation.toLocaleString('ru-RU') + ' монет';
                document.getElementById('item-popup-image').src = itemImage;

                document.getElementById('item-info-popup').classList.add('show');
            });
        });
    }
}

function showNotificationPopup(title, image, message, isError = false) {
    const popup = document.getElementById('purchase-popup');
    popup.classList.toggle('error', isError);
    const loader = document.getElementById('loader');
    const showPopup = () => {
        const popup = document.getElementById('purchase-popup');
        const itemNameElement = document.getElementById('popup-item-name');
        const itemImageElement = document.getElementById('popup-item-image');
        const messageElement = document.getElementById('popup-message');

        itemNameElement.textContent = title;
        itemImageElement.src = image;
        messageElement.textContent = message;
        popup.classList.add('show');

        const rect = popup.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const numSparkles = 20;

        for (let i = 0; i < numSparkles; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = isError ? 'sparkle error-sparkle' : 'sparkle';
            const side = Math.floor(Math.random() * 4);
            let x, y;
            switch (side) {
                case 0: x = Math.random() * width; y = 0; break;
                case 1: x = width; y = Math.random() * height; break;
                case 2: x = Math.random() * width; y = height; break;
                case 3: x = 0; y = Math.random() * height; break;
            }
            sparkle.style.left = `${x}px`;
            sparkle.style.top = `${y}px`;
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 60 + 30;
            const dx = Math.cos(angle) * distance;
            const dy = Math.sin(angle) * distance;
            sparkle.style.setProperty('--x', `${dx}px`);
            sparkle.style.setProperty('--y', `${dy}px`);
            popup.appendChild(sparkle);
            setTimeout(() => sparkle.remove(), 5000);
        }

        setTimeout(() => {
            popup.classList.remove('show');
        }, 3000);
    };

    if (loader.classList.contains('hidden')) {
        showPopup();
    } else {
        const interval = setInterval(() => {
            if (loader.classList.contains('hidden')) {
                clearInterval(interval);
                showPopup();
            }
        }, 100);
    }
}

function setupBuyButtons(userId) {
    document.querySelectorAll('.buy-button').forEach(button => {
        button.addEventListener('click', async function () {
            const row = this.closest('tr');
            const itemName = row.querySelector('td:nth-child(2)').textContent.trim();
            const itemImage = row.querySelector('td:nth-child(1) img').src;
            const costText = this.querySelector('span').textContent;
            const itemCost = parseInt(costText.replace(/\D/g, ''), 10);

            const response = await fetch('/buy_item', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    item_name: itemName,
                    item_cost: itemCost,
                    item_generation: parseInt(row.querySelector('td:nth-child(3)').textContent.replace(/\D/g, ''), 10)                })
            });

            const data = await response.json();
            if (data.status === "success") {
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
                showNotificationPopup(itemName, itemImage, 'Успешно добавлено в инвентарь!');
            } else {
                showNotificationPopup("Ошибка", itemImage, data.message || 'Произошла ошибка!', true);
            }
        });
    });
}

async function loadMarket() {
    const response = await fetch('/get_market');
    const data = await response.json();
    if (data.status === "success") {
        const tbody = document.querySelector('.market-table tbody');
        tbody.innerHTML = '';
        data.items.forEach(item => {
            const row = tbody.insertRow();
            const imgCell = row.insertCell(0);
            const img = document.createElement('img');
            img.src = item.image_path;
            img.alt = item.name;
            img.style.width = '50px';
            imgCell.appendChild(img);
            row.insertCell(1).textContent = item.name;
            row.insertCell(2).textContent = formatNumber(item.generation);
            const priceCell = row.insertCell(3);
            const button = document.createElement('button');
            button.className = 'buy-button';
            button.innerHTML = `<span>${formatNumber(item.price)}</span><img src="/static/bitcoin.png" alt="bitcoin">`;
            priceCell.appendChild(button);
        });
        setupBuyButtons(userId);
    }
}

async function loadRating() {
    try {
        const response = await fetch(`/get_rating`);
        const data = await response.json();
        if (data.status === "success") {
            const ratingTable = document.querySelector('.rating-table tbody');
            ratingTable.innerHTML = '';
            data.users.forEach(user => {
                const newRow = ratingTable.insertRow(-1);
                newRow.insertCell(0).textContent = user.position;
                newRow.insertCell(1).textContent = user.username || 'Anonymous';
                newRow.insertCell(2).textContent = Number(user.balance).toLocaleString('ru-RU');
            });
        }
    } catch (error) {
        console.error('Ошибка при загрузке рейтинга:', error);
    }
}

function hideAllSections() {
    document.querySelector('.main').style.display = 'none';
    document.querySelector('.widgets-container').style.display = 'none';
    document.getElementById('auction').style.display = 'none';
    document.getElementById('rating').style.display = 'none';
    document.getElementById('inventory').style.display = 'none';
    document.getElementById('mart').style.display = 'none';
    document.getElementById('donate').style.display = 'none';
}

const prizes = ["x3 токенов", "1000 токенов", "Drinking Water Dispenser", "10000 токенов", "100000 токенов", "2000 токенов", "Humanoid robot", "x2 токенов"];
const probabilities = [16, 16, 2, 16, 16, 16, 2, 16];

function getRandomIndex() {
    const total = probabilities.reduce((sum, prob) => sum + prob, 0);
    let random = Math.random() * total;
    for (let i = 0; i < probabilities.length; i++) {
        if (random < probabilities[i]) return i;
        random -= probabilities[i];
    }
    return probabilities.length - 1;
}

let isSpinning = false;
async function startSpin() {
    if (isSpinning) return;
    const userId = new URLSearchParams(window.location.search).get('user_id');
    if (!userId) {
        alert("Не удалось определить пользователя");
        return;
    }
    isSpinning = true;
    const wheel = document.getElementById('wheel');
    const sectors = prizes.length;
    const sectorAngle = 360 / sectors;
    const targetIndex = getRandomIndex();
    const extraRotations = 5;
    const finalAngle = (extraRotations * 360) + (targetIndex * sectorAngle) + (sectorAngle / 2);
    wheel.style.transition = 'none';
    wheel.style.transform = `rotate(${0}deg)`;
    setTimeout(() => {
        wheel.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
        wheel.style.transform = `rotate(${-finalAngle}deg)`;
    }, 10);
    try {
        const response = await fetch('/spin_wheel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, prize_index: targetIndex })
        });
        const data = await response.json();
        setTimeout(() => {
            if (data.status === "success") {
                let prizeType, prizeValue, prizeImage;
                if (data.prize.includes("токенов")) {
                    prizeType = "token";
                    const match = data.prize.match(/(x?\d+)\s*токенов/);
                    prizeValue = match ? match[1] : "Неизвестно";
                    prizeImage = "/static/bitcoin.png";
                } else {
                    prizeType = "item";
                    prizeValue = data.prize;
                    prizeImage = `/static/img-market/${data.prize.replace(/ /g, '_').toLowerCase()}.png`;
                }

                if (data.refund) {
                    message = `Предмет "${data.prize}" уже есть в вашем инвентаре. Стоимость вращения (100 монет) возвращена. Ваш баланс: ${data.new_balance}`;
                }
                document.getElementById('currency-amount').textContent = data.new_balance;
                if (prizeType === "token") {
                    const displayValue = data.prize.includes("x") ? `${prizeValue}` : prizeValue;
                    showNotificationPopup(
                        `${displayValue} токенов`,
                        "/static/bitcoin.png",
                        'Вы выиграли токены!'
                    );
                } else if (prizeType === "item") {
                    showNotificationPopup(prizeValue, prizeImage, 'Вы выиграли предмет!');
                }
                if ((data.prize === "Drinking Water Dispenser" || data.prize === "Humanoid robot") && !data.refund) {
                    loadInventory(userId);
                }
            } else {
                alert(`Ошибка: ${data.message}`);
                wheel.style.transition = 'none';
                wheel.style.transform = `rotate(${0}deg)`;
            }
            isSpinning = false;
        }, 4050);
    } catch (error) {
        console.error('Ошибка при вращении колеса:', error);
        alert('Произошла ошибка при соединении с сервером');
        wheel.style.transition = 'none';
        wheel.style.transform = `rotate(${0}deg)`;
        isSpinning = false;
    }
}

let selectedCell = null;
let isGameActive = false;
const CELL_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#FF9F76', '#D4A5A5', '#A283C4'
];

document.querySelectorAll('.game-cell').forEach(cell => {
    cell.addEventListener('click', () => {
        if (!isGameActive) {
            if (selectedCell) selectedCell.classList.remove('selected');
            selectedCell = cell;
            cell.classList.add('selected');
        }
    });
});

async function startGame() {
    if (!selectedCell) {
        alert('Выберите блок!');
        return;
    }

    document.querySelectorAll('.game-cell').forEach((cell, index) => {
        cell.style.backgroundColor = CELL_COLORS[index];
        cell.style.borderColor = CELL_COLORS[index];
    });

    const userId = new URLSearchParams(window.location.search).get('user_id');
    const betInput = document.getElementById('game-bet');
    const betAmount = parseInt(betInput.value);
    const selectedCellIndex = parseInt(selectedCell.dataset.index);

    if (!betAmount || betAmount < 1) {
        alert('Введите корректную ставку!');
        return;
    }

    if (isGameActive) return;
    isGameActive = true;

    try {
        const response = await fetch('/play_game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, bet: betAmount, selected_cell: selectedCellIndex })
        });

        if (!response.ok) throw new Error(`Ошибка: ${response.statusText}`);

        const data = await response.json();
        if (data.status === "error") {
            alert(data.message);
            isGameActive = false;
            return;
        }

        let current = 0;
        const totalSteps = 15;
        const cells = document.querySelectorAll('.game-cell');

        for (let i = 0; i < totalSteps; i++) {
            await new Promise(resolve => setTimeout(resolve, 100 + (i * 20)));
            cells.forEach(c => c.classList.remove('active'));
            current = (current + 1) % 8;
            cells[current].classList.add('active');
        }

        const resultCell = document.querySelector(`[data-index="${data.winning_cell}"]`);
        resultCell.classList.add(data.result === "win" ? 'winner' : 'loser');

        if (data.result === "win") {
            showNotificationPopup(
                "Победа!",
                "/static/bitcoin.png",
                `+${betAmount * 2} монет`,
                false
            );
        } else {
            showNotificationPopup(
                "Проигрыш",
                "/static/bitcoin.png",
                `-${betAmount} монет`,
                true
            );
        }

        document.getElementById('currency-amount').textContent = data.new_balance;

    } catch (error) {
        alert(error.message || 'Ошибка соединения');
    } finally {
        setTimeout(() => {
            document.querySelectorAll('.game-cell').forEach(c => {
                c.classList.remove('active', 'winner', 'loser', 'selected');
            });
            selectedCell = null;
            isGameActive = false;
            betInput.value = '';
        }, 3000);
    }
}