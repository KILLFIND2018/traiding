const tutorialSteps = [
    // Главная
    {
        section: 'main',
        element: '.currency-display',
        message: 'Welcome to Crypto Tycoon Simulator! This is your balance. You’ll use tokens to buy items and play games.',
        position: 'bottom'
    },
    {
        section: 'main',
        element: '#main',
        message: 'Here you see a room with your bonus items, after each purchase you will see them here.',
        position: 'top'
    },
    /*Меню*/
    {
        section: 'main',
        element: '.button.auction',
        message: 'Visit the auction to buy or sell items with other players.',
        position: 'top'
    },
    {
        section: 'main',
        element: '.button.rating',
        message: 'Check the leaderboard to see how you rank against other players.',
        position: 'top'
    },
    {
        section: 'main',
        element: '.button.inventory',
        message: 'Click here to view your inventory. This is where your items will be stored. You can also see some information about the item by clicking on the corresponding line.',
        position: 'top'
    },
    {
        section: 'main',
        element: '.button.mart',
        message: 'This is the shop! Click here to buy items that generate tokens per hour.',
        position: 'top'
    },
    {
        section: 'main',
        element: '.button.donate',
        message: 'Need more tokens? Click here to buy tokens, watch ads for rewards or invite your friend.',
        position: 'top'
    },
    // Widgets Container Section
    {
        section: 'widgets-container',
        element: '.bitcoin-widget',
        message: 'This widget shows the current Bitcoin price. You can bet on whether it will go up or down!',
        position: 'top'
    },
    {
        section: 'widgets-container',
        element: '#bet-amount',
        message: 'Enter the amount you want to bet here.',
        position: 'top'
    },
    {
        section: 'widgets-container',
        element: '#bet-up',
        message: 'Click here to bet that the Bitcoin price will go up. You will see the result at the end of the timer, yes, it is very exciting.',
        position: 'top'
    },
    {
        section: 'widgets-container',
        element: '#bet-down',
        message: 'Click here to bet that the Bitcoin price will go down. You will see the result at the end of the timer, yes, it is very exciting.',
        position: 'top'
    },
    {
        section: 'widgets-container',
        element: '.reward-timer',
        message: 'This timer shows when you can claim a reward or watch an ad for tokens.',
        position: 'top'
    },
    {
        section: 'widgets-container',
        element: '.nav-button.left#to-main',
        message: 'Click here to return to the main screen.',
        position: 'right'
    },
    // Mart Section
    {
        section: 'mart',
        element: '.market-table',
        message: 'Here you can buy items that generate tokens per hour. Scroll to see all available items.',
        position: 'top'
    },
    {
        section: 'mart',
        element: '.nav-button.right#to-wheel',
        message: 'Try your luck! Click here to spin the wheel or play a guessing game.',
        position: 'left'
    },
    // колесо
    {
        section: 'wheel',
        element: '.wheel',
        message: 'This is the wheel! Spin it for a chance to win tokens or items.',
        position: 'top'
    },
    {
        section: 'wheel',
        element: '.spin-btn',
        message: 'Click on the button and dive into the chance of your luck!',
        position: 'top'
    },
    //Игра угадай блок
    {
        section: 'wheel',
        element: '.grid-game',
        message: 'Play the guessing game by selecting a block and placing a bet.',
        position: 'top'
    },
    {
        section: 'wheel',
        element: '.game-controls',
        message: 'Specify the bet and press the button and test your fortune and intuition!',
        position: 'top'
    },
    {
        section: 'wheel',
        element: '.nav-button.left#to-mart',
        message: 'Click here to return to the shop.',
        position: 'right'
    },
    // Auction Section
    {
        section: 'auction',
        element: '.chat-container',
        message: 'Chat with other players here while browsing auction lots.',
        position: 'top'
    },
    {
        section: 'auction',
        element: '.auction-lots',
        message: 'These are the current lots. You can bid on items or create your own lot.',
        position: 'top'
    },
    {
        section: 'auction',
        element: '.create-lot',
        message: 'Select an item from your inventory, enter a starting bid and description. Then you will see your lot and you can decide whether to close the lot or sell it for more!',
        position: 'top'
    },
    // Rating Section
    {
        section: 'rating',
        element: '.rating-table',
        message: 'This leaderboard shows the top players by balance.',
        position: 'top'
    },
    // Inventory Section
    {
        section: 'inventory',
        element: '.inventory-table',
        message: 'Here’s your inventory. These items generate tokens per hour for you.',
        position: 'top'
    },
    // Donate Section
    {
        section: 'donate',
        element: '.buy-stars',
        message: 'Buy tokens for Telegram Stars.',
        position: 'top'
    },
    {
        section: 'donate',
        element: '.watch-ad',
        message: 'Watch the video and get a bonus in the form of tokens.',
        position: 'top'
    },
    {
        section: 'donate',
        element: '.invite-friend',
        message: 'Invite a friend to the game and you will receive a MacBook as a gift in your inventory.',
        position: 'top'
    }
];

let currentStep = 0;
let currentSection = 'main';

function startTutorial() {
    // Проверяем, доступен ли Telegram WebApp и DeviceStorage
    const isTelegramEnv = window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.DeviceStorage?.get === 'function';
    
    if (isTelegramEnv) {
        window.Telegram.WebApp.DeviceStorage.get('tutorialCompleted', (error, value) => {
            if (!value) {
                showTutorialStep();
            }
        });
    } else {
        // Fallback на localStorage для браузера или если DeviceStorage недоступен
        if (!localStorage.getItem('tutorialCompleted')) {
            showTutorialStep();
        }
    }
}

function showTutorialStep() {
    if (currentStep >= tutorialSteps.length) {
        endTutorial();
        return;
    }

    const step = tutorialSteps[currentStep];

    // При необходимости перейдите в нужный раздел.
    if (step.section !== currentSection) {
        switchSection(step.section);
        currentSection = step.section;
        // Подождите, пока раздел станет видимым, прежде чем продолжить.
        setTimeout(() => {
            showTutorialStepContent(step);
        }, 500); // При необходимости отрегулируйте задержку для анимации перехода.
    } else {
        showTutorialStepContent(step);
    }
}

async function showTutorialStepContent(step) {
    // Проверка видимости целевого элемента
    const elementIsVisible = (element) => {
        const rect = element.getBoundingClientRect();
        return !!(rect.top < window.innerHeight && rect.bottom > 0 && 
                rect.left < window.innerWidth && rect.right > 0);
    };

    let targetElement;
    let attempts = 0;
    const maxAttempts = 10;
    
    // Ожидание появления элемента с таймаутом
    while (attempts < maxAttempts) {
        targetElement = document.querySelector(step.element);
        if (targetElement && elementIsVisible(targetElement)) break;
        
        await new Promise(resolve => setTimeout(resolve, 300));
        attempts++;
    }

    if (!targetElement || attempts >= maxAttempts) {
        console.warn(`Element ${step.element} not found, skipping step`);
        currentStep++;
        return showTutorialStep();
    }

    // Прокрутка с оптимизацией для мобильных устройств
    const scrollOptions = {
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
    };

    // Для мобильных - полифилл smooth scroll
    if ('scrollBehavior' in document.documentElement.style) {
        targetElement.scrollIntoView(scrollOptions);
    } else {
        const offset = targetElement.getBoundingClientRect().top + window.scrollY - 100;
        window.scrollTo({ top: offset });
    }

    // Ожидание завершения прокрутки
    await new Promise(resolve => setTimeout(resolve, 800));

    // Создание элементов интерфейса
    const overlay = document.createElement('div');
    overlay.className = 'tutorial-overlay';
    overlay.style.willChange = 'opacity'; // Оптимизация анимации
    
    const highlight = document.createElement('div');
    highlight.className = 'tutorial-highlight';
    highlight.style.willChange = 'transform'; // Оптимизация анимации

    // Рассчет позиции с учетом скролла
    const rect = targetElement.getBoundingClientRect();
    highlight.style.cssText = `
        width: ${rect.width}px;
        height: ${rect.height}px;
        top: ${rect.top + window.scrollY}px;
        left: ${rect.left + window.scrollX}px;
    `;

    // Создание тултипа
    const tooltip = document.createElement('div');
    tooltip.className = `tutorial-tooltip ${step.position}`;
    tooltip.innerHTML = `
        <p>${step.message}</p>
        <button class="tutorial-next">Next</button>
    `;
    tooltip.style.willChange = 'transform'; // Оптимизация анимации

    // Добавление элементов в DOM
    document.body.append(overlay, highlight, tooltip);
    positionTooltip(tooltip, rect, step.position);

    // Обработчик следующего шага
    const nextHandler = async () => {
        overlay.remove();
        highlight.remove();
        tooltip.remove();
        currentStep++;
        
        // Задержка для завершения анимаций
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Проверка видимости перед следующим шагом
        const nextStepElement = document.querySelector(tutorialSteps[currentStep]?.element);
        if (nextStepElement && !elementIsVisible(nextStepElement)) {
            await switchSection(tutorialSteps[currentStep].section);
        }
        
        showTutorialStep();
    };

    // Назначение обработчиков
    tooltip.querySelector('.tutorial-next').addEventListener('click', nextHandler);
    overlay.addEventListener('click', nextHandler);

    // Автоматический переход при бездействии (30 сек)
    const timeout = setTimeout(nextHandler, 30000);
    tooltip.addEventListener('click', () => clearTimeout(timeout));
}

function positionTooltip(tooltip, rect, position) {
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const minMargin = 10;

    let top, left;

    switch (position) {
        case 'top':
            top = rect.top + window.scrollY - tooltipRect.height - 10;
            left = rect.left + window.scrollX + (rect.width - tooltipRect.width) / 2;
            break;
        case 'bottom':
            top = rect.bottom + window.scrollY + 10;
            left = rect.left + window.scrollX + (rect.width - tooltipRect.width) / 2;
            break;
        case 'left':
            top = rect.top + window.scrollY + (rect.height - tooltipRect.height) / 2;
            left = rect.left + window.scrollX - tooltipRect.width - 10;
            break;
        case 'right':
            top = rect.top + window.scrollY + (rect.height - tooltipRect.height) / 2;
            left = rect.left + window.scrollX + rect.width + 10;
            break;
    }

    // регулирование положения, чтобы оставаться в пределах области просмотра
    if (left < minMargin) {
        left = minMargin;
    } else if (left + tooltipRect.width > viewportWidth - minMargin) {
        left = viewportWidth - tooltipRect.width - minMargin;
    }

    if (top < minMargin) {
        top = minMargin;
    }

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
}

function switchSection(section) {
    // Совопостановление разделы с соответствующими идентификаторами кнопок или прямыми действиями
    const sectionMap = {
        'main': () => showSection('main'),
        'auction': () => document.getElementById('auctionButton').click(),
        'rating': () => document.querySelector('.button.rating').click(),
        'inventory': () => document.querySelector('.button.inventory').click(),
        'mart': () => document.querySelector('.button.mart').click(),
        'wheel': () => document.getElementById('to-wheel').click(),
        'widgets-container': () => document.getElementById('to-widgets').click(),
        'donate': () => document.querySelector('.button.donate').click()
    };

    if (sectionMap[section]) {
        sectionMap[section]();
    }
    return new Promise(resolve => {
        sectionMap[section]();
        setTimeout(resolve, 700); // Ждем завершения анимации
    });
}

function endTutorial() {
    const isTelegramEnv = window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.DeviceStorage?.set === 'function';
    
    const finalizeTutorial = () => {
        localStorage.setItem('tutorialCompleted', 'true'); // Для совместимости
        const overlay = document.createElement('div');
        overlay.className = 'tutorial-overlay';
        document.body.appendChild(overlay);

        const finalMessage = document.createElement('div');
        finalMessage.className = 'tutorial-tooltip center';
        finalMessage.innerHTML = `
            <p>That’s it! You’re ready to play Crypto Tycoon Simulator. Have fun!</p>
            <button class="tutorial-next">Start Playing</button>
        `;
        document.body.appendChild(finalMessage);

        const nextButton = finalMessage.querySelector('.tutorial-next');
        nextButton.addEventListener('click', () => {
            overlay.remove();
            finalMessage.remove();
            switchSection('main');
        });
    };

    if (isTelegramEnv) {
        window.Telegram.WebApp.DeviceStorage.set('tutorialCompleted', 'true', () => {
            finalizeTutorial();
        });
    } else {
        finalizeTutorial();
    }
}