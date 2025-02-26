let model;
let hasOlderPC = false;
let hasSpeaker = false;
let hasServer = false;

let olderPCModel = null;
let speakerModel = null;
let serverModel = null;

// Загрузка модели офиса
loader.load('assets/models/Office.glb', function (gltf) {
    model = gltf.scene;
    model.scale.set(0.95, 0.95, 0.95);
    model.position.set(3.5, 0.5, 0);
    scene.add(model);

    model.rotateY(Math.PI);

    animate();
}, undefined, function (error) {
    console.error('Ошибка загрузки модели офиса:', error);
});

function olderPC() {
    if (!hasOlderPC || olderPCModel !== null) return;

    loader.load('assets/models/RetroPC.glb', function (pcGltf) {
        olderPCModel = pcGltf.scene;
        olderPCModel.scale.set(0.014, 0.014, 0.014);
        olderPCModel.position.set(-2.7, 0.5, -2.5);
        scene.add(olderPCModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Older PC":', error);
    });
}

function speaker() {
    if (!hasSpeaker || speakerModel !== null) return;

    loader.load('assets/models/Speaker.glb', function (spGltf) {
        speakerModel = spGltf.scene;
        speakerModel.scale.set(0.001, 0.001, 0.001);
        speakerModel.position.set(-1, 0.5, -2.8);
        scene.add(speakerModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Speaker":', error);
    });
}

function server() {
    if (!hasServer || serverModel !== null) return;

    loader.load('assets/models/ServerV2+console.glb', function (serverGltf) {
        serverModel = serverGltf.scene;
        serverModel.scale.set(0.2, 0.2, 0.2);
        serverModel.position.set(0.5, 0.5, -2.8);
        scene.add(serverModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Server":', error);
    });
}



// Базовая генерация: 1 монета в 1 секунду
const BASE_GENERATION = 1;

// Функция для покупки предмета
function setupBuyButtons() {
    document.querySelectorAll('.buy-button').forEach(button => {
      button.addEventListener('click', function () {
        const row = this.closest('tr');
        const itemName = row.querySelector('td:nth-child(1)').textContent;
        const itemGenerationPerHour = parseInt(row.querySelector('td:nth-child(2)').textContent, 10);
        const itemCost = parseInt(row.querySelector('.buy-button span').textContent, 10);

        const currencyAmount = document.getElementById('currency-amount');
        let currentBalance = parseInt(currencyAmount.textContent, 10);

        if (currentBalance >= itemCost) {
          currentBalance -= itemCost;
          currencyAmount.textContent = currentBalance;

          const inventoryTable = document.querySelector('.inventory-table');
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

// Функция для обновления общей генерации и отображение моделей
function updateTotalGeneration() {
    const inventoryTable = document.querySelector('.inventory-table');
    let totalGeneration = BASE_GENERATION;

    hasOlderPC = false;
    hasSpeaker = false;
    hasServer = false;

    for (let i = 1; i < inventoryTable.rows.length; i++) {
        let itemName = inventoryTable.rows[i].cells[0].innerText;
        let generationPerHour = parseInt(inventoryTable.rows[i].cells[1].innerText, 10);

        if (!isNaN(generationPerHour)) {
            const generationPer5Seconds = generationPerHour;
            totalGeneration += generationPer5Seconds;
        }

        if (itemName.trim() === "Older PC") {
            hasOlderPC = true;
        } else if (itemName.trim() === "Speaker") {
            hasSpeaker = true;
        } else if (itemName.trim() === "Server") {
            hasServer = true;
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

    balanceInterval = setInterval(() => {
        let currentBalance = parseInt(currencyAmount.textContent, 10);
        currentBalance += totalGeneration;
        currencyAmount.textContent = Math.floor(currentBalance);
    }, 1000);
}