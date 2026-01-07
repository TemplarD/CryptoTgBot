// CryptoTeleBot Frontend Application

const tg = window.Telegram.WebApp;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Инициализация Telegram WebApp
    tg.ready();
    tg.expand();
    
    // Установка темы
    if (tg.themeParams) {
        applyTheme();
    }
    
    // Получение данных пользователя
    const initData = tg.initDataUnsafe;
    const user = initData.user;
    
    if (user) {
        document.getElementById('username').textContent = 
            user.first_name + (user.last_name ? ' ' + user.last_name : '');
    }
    
    // Загрузка данных
    loadDashboardData();
    
    // Установка обработчиков событий
    setupEventListeners();
}

function applyTheme() {
    const root = document.documentElement;
    
    if (tg.themeParams.bg_color) {
        root.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    }
    if (tg.themeParams.text_color) {
        root.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    }
    if (tg.themeParams.button_color) {
        root.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color);
    }
    if (tg.themeParams.button_text_color) {
        root.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color);
    }
}

function setupEventListeners() {
    // Обработка изменений темы
    tg.onEvent('themeChanged', function() {
        applyTheme();
    });
    
    // Обработка изменения размера окна
    tg.onEvent('viewportChanged', function() {
        tg.expand();
    });
}

async function loadDashboardData() {
    try {
        // Параллельная загрузка данных
        const [walletData, signalsData, positionsData] = await Promise.all([
            loadWalletData(),
            loadTradingSignals(),
            loadOpenPositions()
        ]);
        
        updateWalletUI(walletData);
        updateSignalsUI(signalsData);
        updatePositionsUI(positionsData);
        
        // Загрузка графика
        loadPriceChart();
        
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        showError('Не удалось загрузить данные. Попробуйте обновить.');
    }
}

async function loadWalletData() {
    try {
        const response = await apiRequest('/api/v1/wallet/info');
        return response;
    } catch (error) {
        console.error('Ошибка загрузки данных кошелька:', error);
        // Возвращаем mock данные при ошибке
        return {
            address: "EQD...example",
            balance: 125.5,
            usd_value: 627.5
        };
    }
}

async function loadTradingSignals() {
    try {
        const response = await apiRequest('/api/v1/trading/signals');
        return response;
    } catch (error) {
        console.error('Ошибка загрузки сигналов:', error);
        return [];
    }
}

async function loadOpenPositions() {
    try {
        const response = await apiRequest('/api/v1/trading/positions');
        return response;
    } catch (error) {
        console.error('Ошибка загрузки позиций:', error);
        return [];
    }
}

async function loadPriceChart() {
    try {
        const response = await apiRequest('/api/v1/trading/market-data/BTC/USDT');
        updateChart(response);
    } catch (error) {
        console.error('Ошибка загрузки графика:', error);
        // Mock данные для графика
        updateChart({
            symbol: 'BTC/USDT',
            price: 44200,
            change_24h: 2.5
        });
    }
}

function updateWalletUI(data) {
    document.getElementById('ton-balance').textContent = data.balance.toFixed(2);
    document.getElementById('ton-usd').textContent = data.usd_value.toFixed(2);
    
    // Загрузка торгового баланса
    loadTradingBalance();
}

async function loadTradingBalance() {
    try {
        const response = await apiRequest('/api/v1/trading/balance');
        document.getElementById('trading-balance').textContent = response.total_balance.toFixed(2);
        
        // Расчет изменения (mock данные)
        const change = (Math.random() - 0.5) * 10;
        const changeElement = document.getElementById('balance-change');
        changeElement.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
        changeElement.style.color = change >= 0 ? '#4caf50' : '#f44336';
        
    } catch (error) {
        console.error('Ошибка загрузки торгового баланса:', error);
    }
}

function updateSignalsUI(signals) {
    const container = document.getElementById('signals-container');
    
    if (signals.length === 0) {
        container.innerHTML = '<div class="loading">Нет активных сигналов</div>';
        return;
    }
    
    container.innerHTML = signals.map(signal => `
        <div class="signal-card ${signal.action.toLowerCase()}">
            <div class="signal-info">
                <div class="signal-symbol">${signal.symbol}</div>
                <div class="signal-action">${signal.action}</div>
                <div class="signal-confidence">Уверенность: ${(signal.confidence * 100).toFixed(1)}%</div>
            </div>
            <div class="signal-amount">
                <div class="amount">${signal.amount}</div>
                <div class="confidence">${(signal.confidence * 100).toFixed(1)}%</div>
            </div>
        </div>
    `).join('');
}

function updatePositionsUI(positions) {
    const container = document.getElementById('positions-container');
    
    if (positions.length === 0) {
        container.innerHTML = '<div class="loading">Нет открытых позиций</div>';
        return;
    }
    
    container.innerHTML = positions.map(position => `
        <div class="position-card">
            <div class="position-header">
                <div class="position-symbol">${position.symbol}</div>
                <div class="position-side ${position.side.toLowerCase()}">${position.side}</div>
            </div>
            <div class="position-details">
                <div>Размер: ${position.size}</div>
                <div>Вход: $${position.entry_price.toFixed(2)}</div>
                <div>Текущая: $${position.current_price.toFixed(2)}</div>
                <div class="position-pnl ${position.pnl >= 0 ? 'positive' : 'negative'}">
                    P&L: $${position.pnl.toFixed(2)} (${position.pnl_percentage >= 0 ? '+' : ''}${position.pnl_percentage.toFixed(2)}%)
                </div>
            </div>
        </div>
    `).join('');
}

function updateChart(data) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Уничтожаем существующий график если есть
    if (window.priceChart) {
        window.priceChart.destroy();
    }
    
    // Генерация mock данных для графика
    const labels = [];
    const prices = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
        const time = new Date(now - i * 60 * 60 * 1000);
        labels.push(time.getHours() + ':00');
        prices.push(data.price + (Math.random() - 0.5) * 1000);
    }
    
    window.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: data.symbol,
                data: prices,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

async function apiRequest(endpoint) {
    const url = `http://localhost:8000${endpoint}`;
    
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            'X-Telegram-User': tg.initDataUnsafe.user?.id || '',
            'Authorization': `tma ${tg.initData}`
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

function refreshData() {
    // Показываем индикатор загрузки
    document.getElementById('signals-container').innerHTML = '<div class="loading">Обновление...</div>';
    document.getElementById('positions-container').innerHTML = '<div class="loading">Обновление...</div>';
    
    // Перезагрузка данных
    loadDashboardData();
    
    // Вибрация для обратной связи
    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
    }
}

function openSettings() {
    // Вибрация для обратной связи
    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('medium');
    }
    
    // TODO: Реализовать открытие настроек
    alert('Настройки в разработке');
}

function showError(message) {
    // Показываем ошибку пользователю
    if (tg.showPopup) {
        tg.showPopup({
            title: 'Ошибка',
            message: message,
            buttons: [{text: 'OK'}]
        });
    } else {
        alert(message);
    }
}
