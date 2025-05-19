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
                updateSpinCost(userId); // Обновляем цену после прокрутки

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

async function checkSpinAvailability(userId) {
    const spinButton = document.querySelector('.token-spin');
    const spinButtonSpan = spinButton.querySelector('span');
    try {
        const response = await fetch(`/check_spin_status?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "available") {
            await updateSpinCost(userId); // Обновляем цену при доступности
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

async function updateSpinCost(userId) {
    try {
        const response = await fetch(`/get_spin_cost?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "success") {
            const spinButton = document.querySelector('.token-spin');
            const spinButtonSpan = spinButton.querySelector('span');
            spinButtonSpan.textContent = formatNumber(data.spin_cost);
        } else {
            console.error('Ошибка получения цены прокрутки:', data.message);
        }
    } catch (error) {
        console.error('Ошибка при запросе цены прокрутки:', error);
    }
}