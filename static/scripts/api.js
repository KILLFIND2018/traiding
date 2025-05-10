/*остановка генерации в зависимоти поведения пользователя*/
async function stopGeneration(userId) {
    try {
        const response = await fetch('/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        if (data.status === "success") {
            console.log(`Генерация для user_id ${userId} успешно остановлена: ${data.message}`);
        } else {
            console.error(`Ошибка остановки генерации для user_id ${userId}: ${data.message}`);
        }
    } catch (error) {
        console.error(`Ошибка при отправке запроса на остановку для user_id ${userId}: ${error}`);
    }
}
/*запуск генерации в зависимоти поведения пользователя*/
async function startGeneration(userId) {
    try {
        const response = await fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        if (data.status === "success") {
            console.log(`Генерация для user_id ${userId} запущена, начальный баланс: ${data.balance}`);
            return data.balance;
        } else {
            console.error('Ошибка при старте:', data.message);
            return null;
        }
    } catch (error) {
        console.error('Ошибка при запуске генерации:', error);
        return null;
    }
}
/*награда за приглашение друга */
async function checkNewRewards(userId) {
    const response = await fetch(`/get_new_rewards?user_id=${userId}`);
    const data = await response.json();
    if (data.status === "success" && data.rewards.length > 0) {
        data.rewards.forEach(reward => {
            const itemImage = `/static/img-market/${reward.item_name.replace(' ', '_').toLowerCase()}.png`;
            showNotificationPopup(reward.item_name, itemImage, `You received ${reward.item_name} for inviting a friend!`);
            if (reward.item_name === "Macbook" && !models["Macbook"]) {
                macbook();
                models["Macbook"] = true;
            }
        });
        await loadInventory(userId);
    }
}

async function loadAuction(userId) {
    await loadLots();
    await loadChat();
    await loadUserItems(userId);
}
/*получение и загрузка лота*/
async function loadLots() {
    const response = await fetch('/get_auction_lots');
    const data = await response.json();
    if (data.status === "success") {
        const tbody = document.getElementById('lots-table-body');
        tbody.innerHTML = '';
        data.lots.forEach(lot => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = lot.lot_id;
            row.insertCell(1).textContent = lot.item_name;
            row.insertCell(2).textContent = lot.description;
            row.insertCell(3).textContent = lot.start_price;
            row.insertCell(4).textContent = lot.current_bid || 'No bets';
            row.insertCell(5).textContent = lot.seller_username || 'Anonymous';
            const actionCell = row.insertCell(6);
            const bidButton = document.createElement('button');
            bidButton.textContent = 'Place a bet';
            bidButton.classList.add('bid-button', 'auctions-table');
            bidButton.onclick = () => placeBid(lot.lot_id);
            actionCell.appendChild(bidButton);
            if (String(lot.seller_id) === userId) {
                const completeButton = document.createElement('button');
                completeButton.textContent = 'Close lot';
                completeButton.classList.add('complete-button', 'auctions-table');
                completeButton.onclick = () => completeLot(lot.lot_id);
                actionCell.appendChild(completeButton);
            }
        });
    } else {
        console.error('Ошибка загрузки лотов:', data.message);
    }
}
/*получение и закгрузка чата в аукционе*/
async function loadChat() {
    const response = await fetch('/get_chat');
    const data = await response.json();
    if (data.status === "success") {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        data.messages.forEach(msg => {
            const p = document.createElement('p');
            p.textContent = `${msg.username}: ${msg.message} (${new Date(msg.timestamp).toLocaleTimeString()})`;
            chatMessages.appendChild(p);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}
/*отправка сообщения пользователя*/
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message) {
        await fetch('/send_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message })
        });
        input.value = '';
        await loadChat();
    }
}
/*загрузка предмета в аукцион пользователя*/
async function loadUserItems(userId) {
    const response = await fetch(`/get_inventory?user_id=${userId}`);
    const data = await response.json();
    if (data.status === "success") {
        const select = document.getElementById('item-select');
        select.innerHTML = '<option value="">Select Item</option>';
        data.items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.item_name;
            option.textContent = item.item_name;
            select.appendChild(option);
        });
    }
}
/*установка цены лота другого пользователя*/
async function placeBid(lotId) {
    const bidAmount = prompt('Place bet:');
    if (bidAmount && !isNaN(bidAmount)) {
        const response = await fetch('/place_bid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, lot_id: lotId, bid_amount: parseInt(bidAmount) })
        });
        const data = await response.json();
        if (data.status === "success") {
            await loadLots();
        } else {
            alert(data.message);
        }
    }
}
/*завершение лота*/
async function completeLot(lotId) {
    const response = await fetch('/complete_lot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, lot_id: lotId })
    });
    const data = await response.json();
    if (data.status === "success") {
        await loadLots();
        await loadInventory(userId);
    } else {
        alert(data.message);
    }
}
/*инцианализация биткоин-виджет*/
async function initBitcoinWidget(userId) {
    async function updatePrice() {
        const response = await fetch('/get_bitcoin_price');
        const data = await response.json();
        if (data.status === "success") {
            document.getElementById('btc-price').textContent = data.price;
        }
    }
    updatePrice();
    setInterval(updatePrice, 60000);

    const ctx = document.createElement('canvas');
    document.getElementById('bitcoin-graph').appendChild(ctx);
    let prices = [];
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'BTC Price (USD)',
                data: prices,
                borderColor: '#f1c40f',
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff' // Updated font color for legend
                    }
                }
                
            },
            scales: {
                x: { 
                    display: false,
                    ticks: {
                        color: '#fff' // Updated font color for x-axis ticks
                    }
                },
                y: { 
                    beginAtZero: false,
                    ticks: {
                        color: '#fff' // Updated font color for y-axis ticks
                    },
                    title: {
                        display: true,
                        text: 'Price (USD)',
                        color: '#fff' // Updated font color for y-axis title
                    }
                }
            }
        }
    });

    async function updateGraph() {
        const response = await fetch('/get_bitcoin_price');
        const data = await response.json();
        if (data.status === "success") {
            prices.push(data.price);
            if (prices.length > 60) prices.shift();
            chart.data.labels = prices.map((_, i) => i);
            chart.data.datasets[0].data = prices;
            chart.update();
        }
    }
    updateGraph();
    setInterval(updateGraph, 60000);
    /*ставка и таймер кулдауна*/ 
    const betUpButton = document.getElementById('bet-up');
    const betDownButton = document.getElementById('bet-down');
    const betAmountInput = document.getElementById('bet-amount');
    const betTimer = document.getElementById('bet-timer');

    async function checkBetStatus() {
        const response = await fetch(`/check_bitcoin_bet?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "pending") {
            const remaining = data.remaining;
            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            const seconds = Math.floor(remaining % 60);
            betTimer.textContent = ` ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            betUpButton.disabled = true;
            betDownButton.disabled = true;
            betAmountInput.disabled = true;
        } else {
            betTimer.textContent = " Rate available!";
            betUpButton.disabled = false;
            betDownButton.disabled = false;
            betAmountInput.disabled = false;
            if (data.won !== undefined) {
                if (data.won) {
                    showNotificationPopup("You win!", "/static/bitcoin.png", `Your prize: ${data.prize} token`);
                } else {
                    showNotificationPopup("You lose", "/static/bitcoin.png", "Try again!");
                }
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
            }
        }
    }
    checkBetStatus();
    setInterval(checkBetStatus, 1000);
    /*указание ставки*/
    betUpButton.addEventListener('click', async () => {
        const amount = parseInt(betAmountInput.value);
        if (amount > 0) {
            const response = await fetch('/place_bitcoin_bet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, bet_amount: amount, bet_direction: 'up' })
            });
            const data = await response.json();
            if (data.status === "success") {
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
                checkBetStatus();
            } else {
                alert(data.message);
            }
        } else {
            alert("Please enter the correct bet amount!");
        }
    });

    betDownButton.addEventListener('click', async () => {
        const amount = parseInt(betAmountInput.value);
        if (amount > 0) {
            const response = await fetch('/place_bitcoin_bet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, bet_amount: amount, bet_direction: 'down' })
            });
            const data = await response.json();
            if (data.status === "success") {
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
                checkBetStatus();
            } else {
                alert(data.message);
            }
        } else {
            alert("Please enter the correct bet amount!");
        }
    });
}
/*проверка, статус доступа к награде за вход пользователя*/
async function checkLoginReward(userId) {
    const response = await fetch(`/get_login_reward_status?user_id=${userId}`);
    const data = await response.json();
    const rewardStatus = document.getElementById('reward-status');
    const timerElement = document.querySelector('.reward-timer');
    timerElement.classList.remove('available');

    if (data.status === "available") {
        rewardStatus.textContent = "Available! Click to get!";
        timerElement.classList.add('available');
        timerElement.onclick = () => claimLoginReward(userId);
    } else if (data.status === "pending") {
        const remaining = data.remaining;
        // Преобразуем секунды в часы, минуты и секунды
        const hours = Math.floor(remaining / 3600);
        const minutes = Math.floor((remaining % 3600) / 60);
        const seconds = Math.floor(remaining % 60);
        // Форматируем время в HH:MM:SS
        rewardStatus.textContent = `Available in ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        timerElement.onclick = null;
    } else {
        rewardStatus.textContent = "Error check";
    }
}
/*получение награды за вход пользователя*/
async function claimLoginReward(userId) {
    const response = await fetch('/claim_login_reward', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    const data = await response.json();
    if (data.status === "success") {
        console.log(`Login reward received: ${data.reward} tokens. New balance: ${data.new_balance}`);
        document.getElementById('currency-amount').textContent = data.new_balance;
        showNotificationPopup("Login Reward", "/static/bitcoin.png", `You have received ${data.reward} tokens!`);
        await checkLoginReward(userId);
    } else {
        console.error('Error receiving reward:', data.message);
        alert('Error receiving reward:' + data.message);
    }
}
/*награда за просмотр рекламы пользователем*/
async function rewardUser(amount) {
    const userId = new URLSearchParams(window.location.search).get('user_id');
    const response = await fetch('/reward_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, amount })
    });
    const data = await response.json();
    if (data.status === 'success') {
        document.getElementById('currency-amount').textContent = data.new_balance;
        showNotificationPopup('Reward', '/static/bitcoin.png', `You have received ${amount} tokens!`);
    } else {
        alert('Reward calculation error: ' + data.message);
    }
}