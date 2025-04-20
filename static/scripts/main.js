const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('user_id');

async function startApp(userId) {
    if (!userId) {
        console.error("User ID отсутствует в URL.");
        document.getElementById('loader').classList.add('hidden');
        return;
    }

    const loader = document.getElementById('loader');
    loader.classList.remove('hidden');

    const initialBalance = await startGeneration(userId);
    if (initialBalance !== null) {
        document.getElementById('currency-amount').textContent = Number(initialBalance).toLocaleString('ru-RU');
    }

    const balanceInterval = setInterval(async () => {
        try {
            const response = await fetch(`/get_balance?user_id=${userId}`);
            const data = await response.json();
            if (data.status === "success") {
                document.getElementById('currency-amount').textContent = Number(data.balance).toLocaleString('ru-RU');
                console.log(`Обновление баланса для user_id ${userId}: ${data.balance}`);
            }
        } catch (error) {
            console.error('Ошибка при обновлении баланса:', error);
        }
    }, 5000);  // Обновление каждые 5 секунд

    const ratingInterval = setInterval(() => {
        loadRating();
    }, 30000);

    const heartbeatInterval = setInterval(async () => {
        try {
            await fetch('/heartbeat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            console.log(`Heartbeat отправлен для user_id ${userId}`);
        } catch (error) {
            console.error(`Ошибка heartbeat для user_id ${userId}: ${error}`);
        }
    }, 5000);

    await checkNewRewards(userId);
    await checkLoginReward(userId);
    const rewardCheckInterval = setInterval(() => checkLoginReward(userId), 1000);

    const inventoryCheckInterval = setInterval(async () => {
        await loadInventory(userId);
    }, 10000);

    Telegram.WebApp.onEvent('web_app_close', async () => {
        console.log('Web App закрыт через Telegram');
        clearInterval(balanceInterval);
        clearInterval(ratingInterval);
        clearInterval(heartbeatInterval);
        clearInterval(inventoryCheckInterval);
        await stopGeneration(userId);
        clearInterval(rewardCheckInterval);
    });

    document.addEventListener('visibilitychange', async () => {
        if (document.visibilityState === 'hidden') {
            console.log('Вкладка стала невидимой');
            clearInterval(balanceInterval);
            clearInterval(ratingInterval);
            clearInterval(heartbeatInterval);
            clearInterval(inventoryCheckInterval);
            await stopGeneration(userId);
            clearInterval(rewardCheckInterval);
        } else if (document.visibilityState === 'visible') {
            console.log('Вкладка снова видима, перезапуск генерации');
            const balance = await startGeneration(userId);
            if (balance !== null) {
                document.getElementById('currency-amount').textContent = balance;
            }
            loadRating();
            await checkNewRewards(userId);
            rewardCheckInterval = setInterval(() => checkLoginReward(userId), 1000);
        }
    });

    window.addEventListener('beforeunload', (event) => {
        console.log('Закрытие вкладки');
        clearInterval(balanceInterval);
        clearInterval(ratingInterval);
        clearInterval(heartbeatInterval);
        clearInterval(inventoryCheckInterval);
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/stop', false);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({ user_id: userId }));
        console.log('Синхронный запрос на остановку отправлен');
        clearInterval(rewardCheckInterval);
    });

    await loadInventory(userId);
    await loadMarket();
    await loadRating();
    await initBitcoinWidget(userId);
    loadAuction(userId);

    await new Promise(resolve => setTimeout(resolve, 10000));
    loader.classList.add('hidden');
}

if (userId) startApp(userId);

if (!localStorage.getItem('swipeHintShown')) {
    const hint = document.createElement('div');
    hint.textContent = '← Свайпайте → чтобы увидеть больше';
    hint.style.position = 'absolute';
    hint.style.bottom = '10px';
    hint.style.color = '#7FFFD4';
    hint.style.fontSize = '14px';
    marketWrapper.appendChild(hint);

    setTimeout(() => hint.remove(), 3000);
    localStorage.setItem('swipeHintShown', 'true');
}