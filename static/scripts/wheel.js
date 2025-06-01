let isSpinning = false;
const prizes = ["x3 tokens", "1000 tokens", "Drinking Water Dispenser", "10000 tokens", "100000 tokens", "2000 tokens", "Humanoid robot", "x2 tokens"];
const probabilities = [5, 28, 2, 20, 10, 28, 2, 5];



/*рандом по шансам колеса*/
function getRandomIndex() {
    const total = probabilities.reduce((sum, prob) => sum + prob, 0);
    let random = Math.random() * total;
    for (let i = 0; i < probabilities.length; i++) {
        if (random < probabilities[i]) return i;
        random -= probabilities[i];
    }
    return probabilities.length - 1;
}

let userTonAddress = null;

async function fetchUserTonAddress(userId) {
  try {
    const res = await fetch('/get_wallet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (data.status === 'success') {
      userTonAddress = data.ton_address;
    }
  } catch (e) {
    console.error("Не удалось получить TON-адрес пользователя", e);
  }
}



async function startSpin(spinType) {
  if (isSpinning) return;
  isSpinning = true;

  const userId = new URLSearchParams(window.location.search).get('user_id');
  if (!userId) {
    showNotificationPopup("Ошибка", "/static/ton_icon.png", "Не удалось определить пользователя", true);
    isSpinning = false;
    return;
  }

  // ─── TON-спин ────────────────────────────────────────────────────────────
  if (spinType === 'ton') {
    try {
      // 1) Создаём pending-транзакцию в базе
      const initRes = await fetch('/initiate_ton_spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      const initData = await initRes.json();
      if (initData.status !== 'success') {
        throw new Error(initData.message || 'Ошибка инициации TON-спина');
      }
      const transactionId = initData.transaction_id;

      // 2) Передаём транзакцию боту, чтобы он выставил инвойс
      await Telegram.WebApp.sendData(`spin_ton_${transactionId}`);

      // 3) После успешной оплаты: отправляем на сервер готовый спин
      const resp = await fetch('/spin_wheel_ton', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          transaction_id: transactionId
        })
      });
      const data = await resp.json();
      if (data.status !== 'success') {
        throw new Error(data.message || 'Ошибка выполнения TON-спина');
      }

      // 4) Анимация колеса по data.prize_index
      const idx        = data.prize_index;
      const finalAngle = (5 * 360) + (idx * 45) + 22.5;
      const wheel      = document.getElementById('wheel');

      wheel.style.transition = 'none';
      wheel.style.transform  = 'rotate(0deg)';

      setTimeout(() => {
        wheel.style.transition = 'transform 4s cubic-bezier(0.25,0.1,0.25,1)';
        wheel.style.transform  = `rotate(-${finalAngle}deg)`;
      }, 10);

      // 5) Показ уведомления и обновление баланса
      setTimeout(() => {
        const { prize, new_balance, ton_prize } = data;
        document.getElementById('currency-amount').textContent = new_balance;
        let message = `Вы выиграли ${prize}!`;
        if (ton_prize) message += ` + ${ton_prize} TON`;
        showNotificationPopup(prize, "/static/img_whell/ton_symbol.png", message);
        updateSpinCost(userId);
        isSpinning = false;
      }, 4050);

    } catch (err) {
      console.error('TON-спин не удался:', err);
      showNotificationPopup("Ошибка", "/static/ton_icon.png", err.message, true);
      isSpinning = false;
    }
    return;
  }

  // ─── Токен-спин ───────────────────────────────────────────────────────────
  const targetIndex = getRandomIndex();
  const finalAngle  = (5 * 360) + (targetIndex * 45) + 22.5;
  const wheel       = document.getElementById('wheel');

  wheel.style.transition = 'none';
  wheel.style.transform  = 'rotate(0deg)';
  setTimeout(() => {
    wheel.style.transition = 'transform 4s cubic-bezier(0.25,0.1,0.25,1)';
    wheel.style.transform  = `rotate(-${finalAngle}deg)`;
  }, 10);

  try {
    const resp = await fetch('/spin_wheel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, prize_index: targetIndex })
    });
    const data = await resp.json();

    setTimeout(() => {
      if (data.status === "success") {
        document.getElementById('currency-amount').textContent = data.new_balance;
        showNotificationPopup(`You win ${data.prize}!`, "/static/bitcoin.png");
        updateSpinCost(userId);
      } else {
        showNotificationPopup("Ошибка", "/static/ton_icon.png", data.message, true);
      }
      isSpinning = false;
    }, 4050);
  } catch (err) {
    console.error('Ошибка токен-спина:', err);
    showNotificationPopup("Ошибка", "/static/ton_icon.png", "Ошибка подключения", true);
    isSpinning = false;
  }
}


// ─── Помощник: опрашиваем Flask о результате TON-спина ─────────────────────
async function pollForSpinResult(transactionId, userId) {
    const wheel = document.getElementById('wheel');
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/get_spin_result?transaction_id=${transactionId}`);
            const json = await res.json();

            if (json.status === 'pending') {
                // ещё не готово — ждём
                return;
            }
            clearInterval(interval);

            if (json.status !== 'success') {
                throw new Error(json.message || 'Неизвестная ошибка спина');
            }

            // ─── Запускаем анимацию колеса ───────────────────────────────
            const prizeIndex = json.prize_index;
            const finalAngle = (5 * 360) + (prizeIndex * 45) + 22.5;
            wheel.style.transition = 'none';
            wheel.style.transform = 'rotate(0deg)';
            setTimeout(() => {
                wheel.style.transition = 'transform 4s cubic-bezier(0.25,0.1,0.25,1)';
                wheel.style.transform = `rotate(-${finalAngle}deg)`;
            }, 10);

            // ─── Показ результата ───────────────────────────────────────
            setTimeout(() => {
                const { prize, new_balance, ton_prize } = json;
                document.getElementById('currency-amount').textContent = new_balance;
                let msg = `Вы выиграли ${prize}!`;
                if (ton_prize) msg += ` + ${ton_prize} TON`;
                showNotificationPopup(prize, "/static/img_whell/ton_symbol.png", msg);
                updateSpinCost(userId);
                isSpinning = false;
            }, 4050);

        } catch (err) {
            clearInterval(interval);
            console.error('Ошибка при опросе результата:', err);
            showNotificationPopup("Ошибка", "/static/ton_symbol.png", err.message, true);
            isSpinning = false;
        }
    }, 1000);
}
async function checkSpinAvailability(userId) {
    const spinButton = document.querySelector('.token-spin');
    const spinButtonSpan = spinButton.querySelector('span');
    try {
        const response = await fetch(`/check_spin_status?user_id=${userId}`);
        const data = await response.json();
        if (data.status === "available") {
            await updateSpinCost(userId);
            spinButton.disabled = false;
            spinButton.classList.add('available');
        } else if (data.status === "pending") {
            const remaining = data.remaining;
            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            const seconds = Math.floor(remaining % 60);
            spinButtonSpan.textContent = `Left ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
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
/*
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
*/
async function updateSpinCost(userId) {
    try {
        const response = await fetch(`/get_spin_cost?user_id=${userId}`);
        const data = await response.json();
        const spinButtonSpan = document.querySelector('.token-spin span');

        if (data.status === "success" && typeof data.spin_cost === "number") {
            spinButtonSpan.textContent = data.spin_cost.toLocaleString('ru-RU');
        } else {
            console.warn("Некорректный ответ от сервера:", data);
            spinButtonSpan.textContent = "—";
        }
    } catch (error) {
        console.error('Ошибка получения стоимости спина:', error);
        const spinButtonSpan = document.querySelector('.token-spin span');
        spinButtonSpan.textContent = "Ошибка";
    }
}

