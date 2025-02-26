// Функция для заполнения таблицы
function fillTable(data) {
    const table = document.querySelector('.market-table');
    const tbody = table.querySelector('tbody') || table; // Если tbody нет, используем саму таблицу

    // Очистка таблицы (кроме заголовков)
    while (tbody.rows.length > 1) {
      tbody.deleteRow(1);
    }

    // Добавление строк из JSON
    data.items.forEach(item => {
      const row = tbody.insertRow();

      // Название предмета
      const nameCell = row.insertCell();
      nameCell.textContent = item.name;

      // Генерация в час
      const generationCell = row.insertCell();
      generationCell.textContent = item.generation;

      // Стоимость (кнопка)
      const priceCell = row.insertCell();
      const button = document.createElement('button');
      button.className = 'buy-button';
      button.innerHTML = `
        <span>${item.price}</span>
        <img src="assets/bitcoin.png" alt="bitcoin">
      `;
      priceCell.appendChild(button);
    });
  }

  

  // Загрузка данных из market.json
  fetch('assets/json/market.json')
    .then(response => {
      if (!response.ok) {
        throw new Error('Ошибка загрузки данных');
      }
      return response.json();
    })
    .then(data => {
      fillTable(data); // Заполняем таблицу данными
      setupBuyButtons(); // Настраиваем кнопки покупки
    })
    .catch(error => {
      console.error('Ошибка:', error);
    });