window.addEventListener('resize', () => {
    const mainElement = document.getElementById('main');
    const width = mainElement.clientWidth;
    const height = mainElement.clientHeight;
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    chart.resize();
});

document.addEventListener('click', function () {
    var music = document.getElementById('background-music');
    music.volume = 0.1;
    music.play();
});

document.getElementById('buyButton').addEventListener('click', () => {
    const tg = window.Telegram.WebApp;
    if (!tg.ready) {
        tg.ready();
    }
    tg.showPopup({
        title: 'Buy tokens for Telegram Stars',
        message: 'Buy 100 tokens for 10 Telegram Stars?',
        buttons: [
            { id: 'buy', type: 'default', text: 'Buy' },
            { type: 'cancel', text: 'Cancel' }
        ]
    }, (buttonId) => {
        if (buttonId === 'buy') {
            const purchaseData = {
                type: 'purchase_stars',
                user_id: urlParams.get('user_id'),
                amount: 100,
                stars_cost: 10
            };
            fetch('/buy_with_stars', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(purchaseData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        tg.showAlert('Purchase successful! 100 tokens added.');
                        document.getElementById('currency-amount').textContent = data.new_balance;
                    } else {
                        tg.showAlert('Purchase Error: ' + (data.message || 'Unknown error'));
                    }
                })
                .catch(error => {
                    tg.showAlert('Purchase Error: ' + error.message);
                });
        }
    });
});

document.getElementById('invite-friend').addEventListener('click', async () => {
    const response = await fetch(`/get_referral_link?user_id=${userId}`);
    const data = await response.json();
    if (data.status === "success") {
        const referralLink = data.referral_link;
        const shareText = `Join me in Crypto Tycoon Simulator! Use this link: ${referralLink}`;
        const shareUrl = `https://t.me/share/url?text=${encodeURIComponent(shareText)}`;
        if (Telegram.WebApp && Telegram.WebApp.openLink) {
            Telegram.WebApp.openLink(shareUrl);
        } else {
            console.error('Telegram WebApp is not available');
            alert('Sharing feature is not available. Make sure you are using the app in Telegram.');
        }
    } else {
        alert('Error getting link');
    }
});

document.getElementById('create-lot-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const lotData = {
        user_id: userId,
        item_name: formData.get('item_name'),
        description: formData.get('description'),
        start_price: parseInt(formData.get('start_price'))
    };
    const response = await fetch('/create_lot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lotData)
    });
    const data = await response.json();
    if (data.status === "success") {
        await loadLots();
        await loadInventory(userId);
        document.getElementById('create-lot-form').reset();
    } else {
        alert(data.message);
    }
});

document.querySelector('.button.auction').addEventListener('click', () => loadAuction(userId));

document.addEventListener('DOMContentLoaded', () => {
    const martContainer = document.querySelector('.mart-container');
    const wheelContainer = document.querySelector('.wheel-container');
    const toWheelButton = document.getElementById('to-wheel');
    const toMartButton = document.getElementById('to-mart');
    const mainContainer = document.querySelector('.main');
    const widgetsContainer = document.querySelector('.widgets-container');
    const toWidgetsButton = document.getElementById('to-widgets');
    const toMainButton = document.getElementById('to-main');

    martContainer.style.display = 'block';
    martContainer.style.opacity = '1';
    martContainer.style.zIndex = '2';
    wheelContainer.style.display = 'none';
    wheelContainer.style.opacity = '0';
    wheelContainer.style.zIndex = '1';

    mainContainer.style.display = 'block';
    mainContainer.style.opacity = '1';
    mainContainer.style.zIndex = '2';
    widgetsContainer.style.display = 'none';
    widgetsContainer.style.opacity = '0';
    widgetsContainer.style.zIndex = '1';

    toWheelButton.addEventListener('click', (event) => {
        event.preventDefault();
        martContainer.style.display = 'none';
        martContainer.style.opacity = '0';
        martContainer.style.zIndex = '1';
        wheelContainer.style.display = 'flex';
        wheelContainer.style.opacity = '1';
        wheelContainer.style.zIndex = '2';
    });

    toMartButton.addEventListener('click', (event) => {
        event.preventDefault();
        wheelContainer.style.display = 'none';
        wheelContainer.style.opacity = '0';
        wheelContainer.style.zIndex = '1';
        martContainer.style.display = 'block';
        martContainer.style.opacity = '1';
        martContainer.style.zIndex = '2';
    });

    toWidgetsButton.addEventListener('click', (event) => {
        event.preventDefault();
        mainContainer.style.display = 'none';
        mainContainer.style.opacity = '0';
        mainContainer.style.zIndex = '1';
        widgetsContainer.style.display = 'block';
        widgetsContainer.style.opacity = '1';
        widgetsContainer.style.zIndex = '2';
    });

    toMainButton.addEventListener('click', (event) => {
        event.preventDefault();
        widgetsContainer.style.display = 'none';
        widgetsContainer.style.opacity = '0';
        widgetsContainer.style.zIndex = '1';
        mainContainer.style.display = 'block';
        mainContainer.style.opacity = '1';
        mainContainer.style.zIndex = '2';
    });
});

document.querySelector('.button.auction').addEventListener('click', function () {
    hideAllSections();
    document.getElementById('auction').style.display = 'block';
    document.querySelector('.button.return').style.display = 'flex';
    document.querySelector('.separator-hidden').style.display = 'block';
});

document.querySelector('.button.rating').addEventListener('click', function () {
    hideAllSections();
    document.getElementById('rating').style.display = 'block';
    document.querySelector('.button.return').style.display = 'flex';
    document.querySelector('.separator-hidden').style.display = 'block';
});

document.querySelector('.button.inventory').addEventListener('click', function () {
    hideAllSections();
    document.getElementById('inventory').style.display = 'block';
    document.querySelector('.button.return').style.display = 'flex';
    document.querySelector('.separator-hidden').style.display = 'block';
});

document.querySelector('.button.mart').addEventListener('click', function () {
    hideAllSections();
    document.getElementById('mart').style.display = 'block';
    document.querySelector('.button.return').style.display = 'flex';
    document.querySelector('.separator-hidden').style.display = 'block';
    const martContainer = document.querySelector('.mart-container');
    const wheelContainer = document.querySelector('.wheel-container');
    martContainer.style.display = 'block';
    martContainer.style.opacity = '1';
    martContainer.style.zIndex = '2';
    wheelContainer.style.display = 'none';
    wheelContainer.style.opacity = '0';
    wheelContainer.style.zIndex = '1';
});

document.querySelector('.button.donate').addEventListener('click', function () {
    hideAllSections();
    document.getElementById('donate').style.display = 'block';
    document.querySelector('.button.return').style.display = 'flex';
    document.querySelector('.separator-hidden').style.display = 'block';
});

document.querySelector('.button.return').addEventListener('click', function () {
    hideAllSections();
    document.querySelector('.button.return').style.display = 'none';
    document.getElementById('main').style.display = 'block';
    document.querySelector('.separator-hidden').style.display = 'none';
    const mainContainer = document.querySelector('.main');
    const widgetsContainer = document.querySelector('.widgets-container');
    mainContainer.style.display = 'block';
    mainContainer.style.opacity = '1';
    mainContainer.style.zIndex = '2';
    widgetsContainer.style.display = 'none';
    widgetsContainer.style.opacity = '0';
    widgetsContainer.style.zIndex = '1';
});

const marketWrapper = document.querySelector('.market');
marketWrapper.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
});

marketWrapper.addEventListener('touchmove', (e) => {
    const touchEndX = e.touches[0].clientX;
    if (Math.abs(touchEndX - touchStartX) > 10) {
        marketWrapper.classList.add('scrollable');
    }
});

marketWrapper.addEventListener('touchend', () => {
    marketWrapper.classList.remove('scrollable');
});

document.querySelector('.close-btn').addEventListener('click', () => {
    document.getElementById('item-info-popup').classList.remove('show');
});

document.getElementById('item-info-popup').addEventListener('click', (e) => {
    if (e.target === document.getElementById('item-info-popup')) {
        document.getElementById('item-info-popup').classList.remove('show');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const toWidgetsButton = document.getElementById('to-widgets');
    const toMainButton = document.getElementById('to-main');
    const toWheelButton = document.getElementById('to-wheel');
    const toMartButton = document.getElementById('to-mart');

    setTimeout(() => {
        toWidgetsButton.classList.add('highlight');
        toMainButton.classList.add('highlight');
        toWheelButton.classList.add('highlight');
        toMartButton.classList.add('highlight');
    }, 10000);

    toWidgetsButton.addEventListener('click', () => {
        toWidgetsButton.classList.remove('highlight');
    });
    toMainButton.addEventListener('click', () => {
        toMainButton.classList.remove('highlight');
    });
    toWheelButton.addEventListener('click', () => {
        toWheelButton.classList.remove('highlight');
    });
    toMartButton.addEventListener('click', () => {
        toMartButton.classList.remove('highlight');
    });
});