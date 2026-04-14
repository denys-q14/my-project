"""
Telegram бот для отримання цін криптовалют
"""
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import httpx
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфігурація
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')
COINGECKO_API_URL = 'https://api.coingecko.com/api/v3'

# Словник криптовалют для пошуку
CRYPTO_IDS = {
    'bitcoin': 'bitcoin',
    'btc': 'bitcoin',
    'ethereum': 'ethereum',
    'eth': 'ethereum',
    'solana': 'solana',
    'sol': 'solana'
}


def get_main_keyboard():
    """
    Створює клавіатуру з кнопками Меню та Довідка
    """
    keyboard = [
        [KeyboardButton("📋 Меню"), KeyboardButton("❓ Довідка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_crypto_price(crypto_id: str) -> dict:
    """
    Отримує поточну ціну криптовалюти з CoinGecko API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{COINGECKO_API_URL}/simple/price',
                params={
                    'ids': crypto_id,
                    'vs_currencies': 'usd,eur,uah',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true',
                    'include_24hr_change': 'true'
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


async def format_price_message(crypto_name: str, crypto_id: str, data: dict) -> str:
    """
    Форматує повідомлення з інформацією про ціну
    """
    if not data or crypto_id not in data:
        return f"❌ Не вдалося отримати дані для {crypto_name}"
    
    crypto_data = data[crypto_id]
    
    message = f"💰 <b>{crypto_name.upper()}</b>\n\n"
    message += f"💵 USD: ${crypto_data.get('usd', 'N/A'):,.2f}\n"
    message += f"€ EUR: €{crypto_data.get('eur', 'N/A'):,.2f}\n"
    message += f"₴ UAH: ₴{crypto_data.get('uah', 'N/A'):,.0f}\n\n"
    
    if 'usd_market_cap' in crypto_data:
        market_cap = crypto_data['usd_market_cap']
        if market_cap:
            message += f"📊 Market Cap: ${market_cap:,.0f}\n"
    
    if 'usd_24h_vol' in crypto_data:
        volume = crypto_data['usd_24h_vol']
        if volume:
            message += f"📈 24h Volume: ${volume:,.0f}\n"
    
    if 'usd_24h_change' in crypto_data:
        change = crypto_data['usd_24h_change']
        if change is not None:
            symbol = "📈" if change >= 0 else "📉"
            message += f"{symbol} 24h Change: {change:+.2f}%"
    
    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /start
    """
    welcome_message = """
👋 Вітаю в Crypto Price Bot!

📌 Доступні команди:
/bitcoin - отримати ціну Bitcoin
/ethereum - отримати ціну Ethereum  
/solana - отримати ціну Solana
/all - отримати ціни всіх трьох криптовалют
/help - показати довідку

Просто введіть команду для отримання поточних цін! 💹
"""
    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /help
    """
    help_message = """
📚 <b>Як користуватися ботом:</b>

<b>Команди для окремих криптовалют:</b>
/bitcoin - ціна Bitcoin (BTC)
/ethereum - ціна Ethereum (ETH)
/solana - ціна Solana (SOL)

<b>Групові команди:</b>
/all - показати ціни всіх трьох криптовалют

<b>Інші команди:</b>
/start - показати привіт
/help - показати цю довідку

💡 Інформація оновлюється в реальному часі з CoinGecko API
"""
    await update.message.reply_text(help_message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def get_bitcoin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /bitcoin
    """
    await update.message.reply_text("⏳ Отримую дані...")
    data = await get_crypto_price('bitcoin')
    message = await format_price_message('Bitcoin', 'bitcoin', data)
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def get_ethereum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /ethereum
    """
    await update.message.reply_text("⏳ Отримую дані...")
    data = await get_crypto_price('ethereum')
    message = await format_price_message('Ethereum', 'ethereum', data)
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def get_solana(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /solana
    """
    await update.message.reply_text("⏳ Отримую дані...")
    data = await get_crypto_price('solana')
    message = await format_price_message('Solana', 'solana', data)
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def get_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник команди /all - отримує ціни всіх трьох криптовалют
    """
    await update.message.reply_text("⏳ Отримую дані для всіх криптовалют...")
    
    # Паралельно отримуємо дані для всіх криптовалют
    bitcoin_data = await get_crypto_price('bitcoin')
    ethereum_data = await get_crypto_price('ethereum')
    solana_data = await get_crypto_price('solana')
    
    message = ""
    message += await format_price_message('Bitcoin', 'bitcoin', bitcoin_data) + "\n\n"
    message += "—" * 30 + "\n\n"
    message += await format_price_message('Ethereum', 'ethereum', ethereum_data) + "\n\n"
    message += "—" * 30 + "\n\n"
    message += await format_price_message('Solana', 'solana', solana_data)
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник натиснення кнопок Меню та Довідка
    """
    user_text = update.message.text
    
    if user_text == "📋 Меню":
        # Показуємо меню команд
        menu_message = """
📋 <b>Меню команд</b>

<b>Вибирайте криптовалюту:</b>
/bitcoin - ціна Bitcoin (BTC)
/ethereum - ціна Ethereum (ETH)
/solana - ціна Solana (SOL)

<b>Групові команди:</b>
/all - показати ціни всіх трьох криптовалют

💹 Введіть команду або натисніть кнопку нижче
"""
        await update.message.reply_text(menu_message, parse_mode='HTML', reply_markup=get_main_keyboard())
    
    elif user_text == "❓ Довідка":
        # Показуємо довідку
        help_message = """
📚 <b>Як користуватися ботом:</b>

<b>Команди для окремих криптовалют:</b>
/bitcoin - ціна Bitcoin (BTC)
/ethereum - ціна Ethereum (ETH)
/solana - ціна Solana (SOL)

<b>Групові команди:</b>
/all - показати ціни всіх трьох криптовалют

<b>Інші команди:</b>
/start - показати привіт
/help - показати цю довідку

💡 Інформація оновлюється в реальному часі з CoinGecko API
"""
        await update.message.reply_text(help_message, parse_mode='HTML', reply_markup=get_main_keyboard())


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробник помилок
    """
    logger.error(f"Помилка під час обробки оновлення {update}: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "😞 Виникла помилка. Спробуйте ще раз пізніше."
        )


def main() -> None:
    """
    Запуск бота
    """
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ПОМИЛКА: Встановіть TELEGRAM_BOT_TOKEN у змінних оточення!")
        print("Приклад: export TELEGRAM_BOT_TOKEN='your_token_here'")
        return

    # Створюємо Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Додаємо обробники команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('bitcoin', get_bitcoin))
    application.add_handler(CommandHandler('ethereum', get_ethereum))
    application.add_handler(CommandHandler('solana', get_solana))
    application.add_handler(CommandHandler('all', get_all))
    
    # Додаємо обробник для натиснення кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press))

    # Додаємо обробник помилок
    application.add_error_handler(error_handler)

    # Запускаємо бота
    print("🚀 Бот стартує...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
