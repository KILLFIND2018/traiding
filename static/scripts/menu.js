/* меню*/
function hideAllSections() {
    document.querySelector('.main').style.display = 'none';
    document.getElementById('auction').style.display = 'none';
    document.getElementById('rating').style.display = 'none';
    document.getElementById('inventory').style.display = 'none';
    document.getElementById('mart').style.display = 'none';
    document.getElementById('donate').style.display = 'none';
}

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
});