# 🤖 Crypto Price Bot

Telegram бот для отримання поточних цін криптовалют: Bitcoin, Ethereum та Solana.

## 📋 Функціонал

- 💰 Отримання поточних цін в USD, EUR та UAH
- 📊 Інформація про Market Cap
- 📈 Дані про 24-годинний обсяг торговлі
- 📉 Відсоток зміни за останні 24 години
- 🔄 Реальні дані з CoinGecko API

## 🚀 Встановлення та запуск

### 1. Клонування репозиторію

```bash
git clone <your-repo-url>
cd my-project
```

### 2. Створення віртуального середовища

```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Отримання Telegram Bot токена

1. Напишіть до [@BotFather](https://t.me/botfather) в Telegram
2. Виконайте команду `/start`
3. Виконайте команду `/newbot`
4. Дайте боту ім'я та username
5. Скопіюйте отриманий токен

### 5. Встановлення змінної оточення

```bash
# На macOS/Linux:
export TELEGRAM_BOT_TOKEN='your_bot_token_here'

# На Windows (Command Prompt):
set TELEGRAM_BOT_TOKEN=your_bot_token_here

# На Windows (PowerShell):
$env:TELEGRAM_BOT_TOKEN='your_bot_token_here'
```

### 6. Запуск бота

```bash
python3 crypto_bot.py
```

Бот почне працювати та буде очікувати команд від користувачів.

## 📝 Доступні команди

| Команда | Описання |
|---------|----------|
| `/start` | Привіт та інформація про бота |
| `/help` | Список всіх доступних команд |
| `/bitcoin` | Получити ціну Bitcoin |
| `/ethereum` | Получити ціну Ethereum |
| `/solana` | Получити ціну Solana |
| `/all` | Получити ціни всіх трьох криптовалют |

## 💡 Приклади використання

### Отримання ціни Bitcoin:
```
Користувач: /bitcoin
Бот: 💰 BITCOIN
     💵 USD: $45,123.45
     € EUR: €41,234.56
     ₴ UAH: ₴1,856,234
     📊 Market Cap: $895,123,456,789
     📈 24h Volume: $23,456,789,012
     📈 24h Change: +2.34%
```

## 🔧 Технологічний стек

- **Python 3.8+**
- **python-telegram-bot** - бібліотека для роботи з Telegram API
- **httpx** - асинхронний HTTP клієнт
- **CoinGecko API** - дані про криптовалюти

## 📊 API

Бот використовує [CoinGecko API](https://www.coingecko.com/api/documentation) для отримання даних про криптовалюти. API є безкоштовним та не вимагає автентифікації.

## ⚙️ Конфігурація

Всі налаштування зберігаються у змінних оточення:

- `TELEGRAM_BOT_TOKEN` - токен вашого Telegram бота

## 🐛 Розв'язування проблем

### Бот не запускається
- Перевірте, що встановлена змінна оточення `TELEGRAM_BOT_TOKEN`
- Перевірте, чи правильний токен

### Не отримуються дані про ціни
- Перевірте интернет-з'єднання
- Перевірте, чи доступний CoinGecko API (він може мати обмеження на кількість запитів)

### ImportError при запуску
- Переконайтесь, що встановлені всі залежності з `requirements.txt`
- Переконайтесь, що активовано віртуальне середовище

## 📦 Розгортування

### Розгортування на Heroku

1. Створіть файл `Procfile`:
```
worker: python crypto_bot.py
```

2. Разгерніть на Heroku:
```bash
heroku create your-app-name
heroku config:set TELEGRAM_BOT_TOKEN='your_token'
git push heroku main
heroku ps:scale worker=1
```

### Розгортування на VPS

Рекомендується використовувати systemd або supervisor для управління процесом бота.

## 📄 Ліцензія

MIT License

## 👨‍💻 Автор

Створено для отримання інформації про криптовалюти через Telegram

## 📞 Підтримка

Для звітів про баги та пропозицій щодо функцій, будь ласка, відкрийте Issue в репозиторії.
