/*отступы в числах*/
function formatNumber(num) {
    return Number(num).toLocaleString('ru-RU');
}
/*Загрузка инвентаря и его механика отображения в таблице*/
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

            // Ячейка для иконки
            const imgCell = newRow.insertCell(0);
            const img = document.createElement('img');
            const imageName = item.item_name.replace(/ /g, '_').toLowerCase() + '.png';
            img.src = `/static/img-market/${imageName}`;
            img.alt = item.item_name;
            img.style.width = '50px'; // Устанавливаем размер как в магазине
            imgCell.appendChild(img);

            // Ячейки для названия, генерации и статуса
            newRow.insertCell(1).textContent = item.item_name;
            newRow.insertCell(2).textContent = formatNumber(item.generation_per_hour);
            newRow.insertCell(3).textContent = 'Active';

            updateTotalGeneration(item.item_name);
        });

        // Слушатели событий для всплывающего окна
        document.querySelectorAll('.inventory-item').forEach(row => {
            row.addEventListener('click', () => {
                const itemName = row.dataset.itemName;
                const generation = parseInt(row.dataset.generation) / 3600;
                const itemImage = `/static/img-market/${itemName.replace(/ /g, '_').toLowerCase()}.png`;

                document.getElementById('item-popup-name').textContent = itemName;
                document.getElementById('item-popup-profit').textContent = generation.toLocaleString('ru-RU') + ' tokens';
                document.getElementById('item-popup-image').src = itemImage;

                document.getElementById('item-info-popup').classList.add('show');
            });
        });
    }
}
/*Показ уведомлений*/
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
/*окно просмотра рекламы*/
function showAdPopup(reward) {
    const popup = document.getElementById('popup-ads');
    const video = document.getElementById('ad-video');
    const closeButton = document.getElementById('close-ad');

    // Скрываем кнопку "Закрыть" при открытии попапа
    closeButton.style.display = 'none';

    popup.style.display = 'block';
    video.play();

    // Показываем кнопку "Закрыть" и начисляем награду после окончания видео
    video.onended = async () => {
        closeButton.style.display = 'block';
        await rewardUser(reward);
    };

    // Обработчик для кнопки "Закрыть"
    closeButton.addEventListener('click', () => {
        popup.style.display = 'none';
        video.pause();
        video.currentTime = 0;
        // Скрываем кнопку "Закрыть" для следующего открытия
        closeButton.style.display = 'none';
    });
}
/*уведомление которое дает выбор на просмотр рекламы за 500 токенов*/
function showAdNotification() {
    const notification = document.createElement('div');
    notification.className = 'ad-notification';
    notification.innerHTML = `
        <p>Watch the ad and get 500 tokens!</p>
        <button id="watch-ad-notification">Watch!</button>
        <button id="close-ad-notification">Close!</button>
    `;
    document.body.appendChild(notification);

    document.getElementById('watch-ad-notification').addEventListener('click', () => {
        showAdPopup(500);
        notification.remove();
    });

    document.getElementById('close-ad-notification').addEventListener('click', () => {
        notification.remove();
    });
}
/*добавление кнопок купить в магазине и его механика*/
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
                    item_generation: parseInt(row.querySelector('td:nth-child(3)').textContent.replace(/\D/g, ''), 10)
                })
            });

            const data = await response.json();
            if (data.status === "success") {
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
                showNotificationPopup(itemName, itemImage, 'Successfully added to inventory!');
            } else {
                showNotificationPopup("Error", itemImage, data.message || 'An error occurred!', true);
            }
        });
    });
}
/*загрузка магазина и его механика отображения*/
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
/*загрузка рейтинга и его механика отображения*/
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
/*слушатель кнопок меню*/
function hideAllSections() {
    document.querySelector('.main').style.display = 'none';
    document.querySelector('.widgets-container').style.display = 'none';
    document.getElementById('auction').style.display = 'none';
    document.getElementById('rating').style.display = 'none';
    document.getElementById('inventory').style.display = 'none';
    document.getElementById('mart').style.display = 'none';
    document.getElementById('donate').style.display = 'none';

    document.querySelector('.game-menu').style.display = 'flex';
}
/*призы колеса */
const prizes = ["x3 tokens", "1000 tokens", "Drinking Water Dispenser", "10000 tokens", "100000 tokens", "2000 tokens", "Humanoid robot", "x2 tokens"];
const probabilities = [5, 28, 2, 20, 10, 28, 2, 5];
/*рандом по шансам колеса */
function getRandomIndex() {
    const total = probabilities.reduce((sum, prob) => sum + prob, 0);
    let random = Math.random() * total;
    for (let i = 0; i < probabilities.length; i++) {
        if (random < probabilities[i]) return i;
        random -= probabilities[i];
    }
    return probabilities.length - 1;
}
/*механика колеса*/
let isSpinning = false;

async function startSpin(spinType) {
    if (isSpinning) return;
    const userId = new URLSearchParams(window.location.search).get('user_id');
    if (!userId) {
        showNotificationPopup("Ошибка", "/static/ton_icon.png", "Не удалось определить пользователя", true);
        return;
    }
    
    isSpinning = true;
    const wheel = document.getElementById('wheel');
    const targetIndex = getRandomIndex();
    const finalAngle = (5 * 360) + (targetIndex * 45) + 22.5;

    wheel.style.transition = 'none';
    wheel.style.transform = `rotate(0deg)`;
    
    setTimeout(() => {
        wheel.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
        wheel.style.transform = `rotate(-${finalAngle}deg)`;
    }, 10);

    try {
        const endpoint = spinType === 'ton' ? '/spin_wheel_ton' : '/spin_wheel';
        const body = { 
            user_id: userId, 
            prize_index: targetIndex,
            ...(spinType === 'ton' && { transaction_id: await simulateTonTransaction(userId) })
        };

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        
        setTimeout(() => {
            if (data.status === "success") {
                let message = `Вы выиграли ${data.prize}!`;
                let prizeImage = "/static/bitcoin.png";

                // Обработка TON-призов
                if (spinType === 'ton' && data.ton_prize > 0) {
                    message += ` + ${data.ton_prize} TON`;
                    prizeImage = "/static/img_whell/ton_symbol.png";
                }

                // Обновление интерфейса
                document.getElementById('currency-amount').textContent = data.new_balance;
                showNotificationPopup(data.prize, prizeImage, message);

                // Обновление кнопки TON
                if (spinType === 'ton') {
                    checkTonSpinAvailability(userId);
                }
            } else {
                showNotificationPopup("Ошибка", "/static/ton_icon.png", data.message, true);
            }
            isSpinning = false;
        }, 4050);

    } catch (error) {
        console.error('Ошибка:', error);
        showNotificationPopup("Ошибка", "/static/ton_icon.png", "Ошибка подключения", true);
        isSpinning = false;
    }
}

// Тестовая функция для симуляции TON-транзакции
async function simulateTonTransaction(userId) {
    const tg = window.Telegram.WebApp;
    return new Promise((resolve, reject) => {
        tg.showPopup({
            title: 'Подтверждение транзакции',
            message: 'Совершить тестовую транзакцию 0.01 TON?',
            buttons: [
                { id: 'confirm', type: 'default', text: 'Подтвердить' },
                { type: 'cancel', text: 'Отмена' }
            ]
        }, (buttonId) => {
            if (buttonId === 'confirm') {
                const transactionId = `TEST_${userId}_${Date.now()}`;
                resolve(transactionId);
            } else {
                reject(new Error('Транзакция отменена'));
            }
        });
    });
}
/*механика угадай блок и его стилизация*/
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
        alert('Select block!');
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
        alert('Please enter a valid bid!');
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

        if (!response.ok) throw new Error(`Error: ${response.statusText}`);

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
                "Win!",
                "/static/bitcoin.png",
                `+ ${betAmount * 2} tokens`,
                false
            );
        } else {
            showNotificationPopup(
                "Lose!",
                "/static/bitcoin.png",
                `- ${betAmount} tokens`,
                true
            );
        }

        document.getElementById('currency-amount').textContent = data.new_balance;

    } catch (error) {
        alert(error.message || 'Error connecting');
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

async function checkSpinAvailability(userId) {
    const spinButton = document.querySelector('.token-spin');
    const spinButtonSpan = spinButton.querySelector('span');
    try {
        const response = await fetch(`/check_spin_status?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "available") {
            spinButtonSpan.textContent = "100";
            spinButton.disabled = false;
            spinButton.classList.add('available');
        } else if (data.status === "pending") {
            const remaining = data.remaining;
            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            const seconds = Math.floor(remaining % 60);
            spinButtonSpan.textContent = `Осталось ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            spinButton.disabled = true;
            spinButton.classList.remove('available');
        } else {
            spinButtonSpan.textContent = "Ошибка";
            spinButton.disabled = true;
            spinButton.classList.remove('available');
        }
    } catch (error) {
        console.error('Ошибка проверки спина:', error);
        spinButtonSpan.textContent = "Ошибка";
        spinButton.disabled = true;
        spinButton.classList.remove('available');
    }
}

async function checkTonSpinAvailability(userId) {
    const tonButton = document.querySelector('.ton-spin');
    const tonButtonSpan = tonButton.querySelector('span');
    try {
        const response = await fetch(`/check_ton_spin_status?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "available") {
            tonButtonSpan.textContent = "0.01";
            tonButton.disabled = false;
            tonButton.classList.add('available');
        } else if (data.status === "pending") {
            const remaining = data.remaining;
            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            const seconds = Math.floor(remaining % 60);
            tonButtonSpan.textContent = `Осталось ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            tonButton.disabled = true;
            tonButton.classList.remove('available');
        } else {
            tonButtonSpan.textContent = "Ошибка";
            tonButton.disabled = true;
            tonButton.classList.remove('available');
        }
    } catch (error) {
        console.error('Ошибка проверки TON спина:', error);
        tonButtonSpan.textContent = "Ошибка";
        tonButton.disabled = true;
        tonButton.classList.remove('available');
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}