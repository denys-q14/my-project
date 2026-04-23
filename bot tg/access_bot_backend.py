import httpx

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from access_bot_common import (
    BOT_TOKEN,
    ADMIN_PANEL_PORT,
    ADMIN_TELEGRAM_IDS,
    COINMARKETCAP_API_KEY,
    COINMARKETCAP_API_URL,
    add_or_update_user,
    get_user_by_telegram_id,
    is_admin_user,
    is_banned_user,
    list_users,
    log_event,
    update_user_role_status,
    remove_user,
    init_db,
)

COINMARKETCAP_HEADERS = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY} if COINMARKETCAP_API_KEY else {}
CMC_SYMBOLS = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'solana': 'SOL',
}


def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton('📋 Меню'), KeyboardButton('❓ Довідка')],
        [KeyboardButton('📈 Ріст')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_crypto_price(crypto_id: str) -> dict | None:
    symbol = CMC_SYMBOLS.get(crypto_id.lower())
    if not symbol:
        return None
    try:
        async with httpx.AsyncClient(headers=COINMARKETCAP_HEADERS) as client:
            response = await client.get(
                f'{COINMARKETCAP_API_URL}/v1/cryptocurrency/quotes/latest',
                params={
                    'symbol': symbol,
                    'convert': 'USD,EUR,UAH'
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json().get('data', {})
            return data.get(symbol)
    except Exception:
        return None


async def get_top_growth(period: str) -> list[dict] | None:
    field = {
        '1h': 'percent_change_1h',
        '24h': 'percent_change_24h',
        '7d': 'percent_change_7d'
    }.get(period)
    if field is None:
        return None

    try:
        async with httpx.AsyncClient(headers=COINMARKETCAP_HEADERS) as client:
            response = await client.get(
                f'{COINMARKETCAP_API_URL}/v1/cryptocurrency/listings/latest',
                params={
                    'start': 1,
                    'limit': 100,
                    'convert': 'USD',
                    'price_change_percentage': '1h,24h,7d'
                },
                timeout=15.0
            )
            response.raise_for_status()
            coins = response.json().get('data', [])
            filtered = [coin for coin in coins if coin.get('quote', {}).get('USD', {}).get(field) is not None]
            filtered.sort(
                key=lambda coin: coin.get('quote', {}).get('USD', {}).get(field, 0),
                reverse=True
            )
            return filtered[:10]
    except Exception:
        return None


def format_growth_list(coins: list[dict], period: str) -> str:
    title = {
        '1h': 'Топ 10 ріст за 1 годину',
        '24h': 'Топ 10 ріст за 24 години',
        '7d': 'Топ 10 ріст за 7 днів'
    }.get(period, 'Топ 10 ріст')

    field = {
        '1h': 'percent_change_1h',
        '24h': 'percent_change_24h',
        '7d': 'percent_change_7d'
    }[period]

    lines = [f'📈 <b>{title}</b>\n']
    for coin in coins:
        quote_usd = coin.get('quote', {}).get('USD', {})
        change = quote_usd.get(field, 0.0)
        price = quote_usd.get('price', 0.0)
        lines.append(
            f'{coin.get("name")} ({coin.get("symbol", "").upper()}): {change:+.2f}% — ${price:,.2f}'
        )
    return '\n'.join(lines)


def format_price_message(crypto_name: str, crypto_id: str, data: dict | None) -> str:
    if not data:
        return f'❌ Не вдалося отримати дані для {crypto_name}'

    quote_usd = data.get('quote', {}).get('USD', {})
    quote_eur = data.get('quote', {}).get('EUR', {})
    quote_uah = data.get('quote', {}).get('UAH', {})

    usd = quote_usd.get('price', 0.0)
    eur = quote_eur.get('price', 0.0)
    uah = quote_uah.get('price', 0.0)

    message = f'💰 <b>{crypto_name.upper()}</b>\n\n'
    message += f'💵 USD: ${usd:,.2f}\n'
    message += f'€ EUR: €{eur:,.2f}\n'
    message += f'₴ UAH: ₴{uah:,.2f}\n\n'

    market_cap = quote_usd.get('market_cap')
    if market_cap is not None:
        message += f'📊 Market Cap: ${market_cap:,.0f}\n'

    volume = quote_usd.get('volume_24h')
    if volume is not None:
        message += f'📈 24h Volume: ${volume:,.0f}\n'

    change_24h = quote_usd.get('percent_change_24h')
    if change_24h is not None:
        symbol = '📈' if change_24h >= 0 else '📉'
        message += f'{symbol} 24h Change: {change_24h:+.2f}%'

    return message


async def growth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_banned_user(update.effective_user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return

    args = context.args
    period = '24h'
    if args:
        normalized = args[0].lower()
        if normalized in ('1h', '24h', '7d'):
            period = normalized
        else:
            await update.message.reply_text(
                'Використання: /growth <1h|24h|7d>\nНаприклад: /growth 24h',
                reply_markup=get_main_keyboard()
            )
            return

    await update.message.reply_text(f'⏳ Отримую топ-10 монет за ростом за {period}...', reply_markup=get_main_keyboard())
    coins = await get_top_growth(period)
    if coins is None:
        await update.message.reply_text(
            'Не вдалося отримати дані про зростання. Спробуйте пізніше.',
            reply_markup=get_main_keyboard()
        )
        return

    message = format_growth_list(coins, period)
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=get_main_keyboard())
    log_event(update.effective_user.id, 'growth', f'period={period} count={len(coins)}')


async def bitcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    change = crypto_data.get('usd_24h_change')
    if change is not None:
        symbol = '📈' if change >= 0 else '📉'
        message += f'{symbol} 24h Change: {change:+.2f}%'

    return message


async def bitcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_banned_user(update.effective_user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    await update.message.reply_text('⏳ Отримую дані для Bitcoin...')
    data = await get_crypto_price('bitcoin')
    message = await format_price_message('Bitcoin', 'bitcoin', data)
    await update.message.reply_text(message, parse_mode='HTML')
    log_event(update.effective_user.id, 'bitcoin', 'requested bitcoin price')


async def ethereum_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_banned_user(update.effective_user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    await update.message.reply_text('⏳ Отримую дані для Ethereum...')
    data = await get_crypto_price('ethereum')
    message = await format_price_message('Ethereum', 'ethereum', data)
    await update.message.reply_text(message, parse_mode='HTML')
    log_event(update.effective_user.id, 'ethereum', 'requested ethereum price')


async def solana_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_banned_user(update.effective_user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    await update.message.reply_text('⏳ Отримую дані для Solana...')
    data = await get_crypto_price('solana')
    message = await format_price_message('Solana', 'solana', data)
    await update.message.reply_text(message, parse_mode='HTML')
    log_event(update.effective_user.id, 'solana', 'requested solana price')


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_banned_user(update.effective_user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    await update.message.reply_text('⏳ Отримую дані для всіх криптовалют...')
    bitcoin_data = await get_crypto_price('bitcoin')
    ethereum_data = await get_crypto_price('ethereum')
    solana_data = await get_crypto_price('solana')

    message = ''
    message += await format_price_message('Bitcoin', 'bitcoin', bitcoin_data) + '\n\n'
    message += '—' * 30 + '\n\n'
    message += await format_price_message('Ethereum', 'ethereum', ethereum_data) + '\n\n'
    message += '—' * 30 + '\n\n'
    message += await format_price_message('Solana', 'solana', solana_data)

    await update.message.reply_text(message, parse_mode='HTML')
    log_event(update.effective_user.id, 'all', 'requested all crypto prices')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    add_or_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role='admin' if user.id in ADMIN_TELEGRAM_IDS else 'guest',
        status='active'
    )
    if is_banned_user(user.id):
        await update.message.reply_text('Доступ заборонено. Зверніться до адміністратора.')
        return

    role = get_user_by_telegram_id(user.id)['role']
    welcome_message = (
        f'👋 Вітаю, {user.first_name or user.username}!\n'
        f'Ваш рівень доступу: {role}.\n\n'
        '📌 Список доступних команд:\n'
        '/bitcoin, /ethereum, /solana, /all\n'
        '/help - показати всі команди\n\n'
        'Використайте кнопки «📋 Меню» або «❓ Довідка» для швидкого вибору.'
    )
    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())
    log_event(user.id, 'start', f'role={role}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ви заблоковані. Зверніться до адміністратора.')
        return

    role = get_user_by_telegram_id(user.id)['role']
    commands = [
        '/start - Привітання та реєстрація',
        '/help - Список команд',
        '/myrole - Ваш рівень доступу',
        '/request - Запросити повний доступ',
        '/bitcoin - Ціна Bitcoin',
        '/ethereum - Ціна Ethereum',
        '/solana - Ціна Solana',
        '/all - Ціни всіх криптовалют',
        '/growth 1h - Топ 10 ріст за 1 годину',
        '/growth 24h - Топ 10 ріст за 24 години',
        '/growth 7d - Топ 10 ріст за 7 днів',
    ]
    if role in ('admin', 'user'):
        commands.append('/status - Перевірити доступ')
    if role == 'admin':
        commands.extend([
            '/adminpanel - Посилання на адміністративну панель',
            '/promote <telegram_id> <role> - Змінити роль користувача',
            '/ban <telegram_id> - Заблокувати користувача',
            '/broadcast <текст> - Розіслати повідомлення',
        ])
    help_text = 'Доступні команди:\n' + '\n'.join(commands) + '\n\n' + 'Використайте кнопки «📋 Меню» або «❓ Довідка» для швидкого доступу.'
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard())
    log_event(user.id, 'help', f'role={role}')


async def myrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    profile = get_user_by_telegram_id(user.id)
    if not profile:
        await update.message.reply_text('Вас не знайдено в базі. Будь ласка, запустіть /start.')
        return
    await update.message.reply_text(
        f"Ваш Telegram ID: {profile['telegram_id']}\n"
        f"Роль: {profile['role']}\n"
        f"Статус: {profile['status']}"
    )
    log_event(user.id, 'myrole', profile['role'])


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = get_user_by_telegram_id(user.id)
    if not profile:
        await update.message.reply_text('Будь ласка, запустіть /start для реєстрації.')
        return
    await update.message.reply_text(
        f"Ваш статус: {profile['status']}\n"
        f"Роль: {profile['role']}"
    )
    log_event(user.id, 'status', profile['status'])


async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = get_user_by_telegram_id(user.id)
    if profile and profile['role'] in ('admin', 'user'):
        await update.message.reply_text('У вас вже є доступ до сервісу.')
        return
    add_or_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role='guest',
        status='pending'
    )
    await update.message.reply_text(
        'Запит на доступ відправлено. Адміністратор перевірить ваш запит протягом найближчого часу.'
    )
    log_event(user.id, 'request', 'requested access')
    admin_message = (
        f'📌 Новий запит на доступ:\n'
        f'User: {user.first_name or user.username} ({user.id})\n'
        f'Telegram: @{user.username if user.username else "не вказано"}\n'
        f'Перейдіть в адмін-панель для підтвердження.'
    )
    for admin_id in ADMIN_TELEGRAM_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)
        except Exception:
            pass


async def adminpanel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin_user(user.id):
        await update.message.reply_text('Ця команда доступна тільки адміністраторам.')
        return
    panel_url = f'http://localhost:{ADMIN_PANEL_PORT}/admin'
    await update.message.reply_text(
        f'Адмін-панель запущена за адресою: {panel_url}\n'
        'Використайте пароль з файлу .env для входу.'
    )
    log_event(user.id, 'adminpanel', 'requested admin panel link')


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin_user(user.id):
        await update.message.reply_text('Тільки адміністратор може змінювати ролі.')
        return
    args = context.args
    if len(args) != 2 or args[1] not in ('guest', 'user', 'admin'):
        await update.message.reply_text('Використання: /promote <telegram_id> <guest|user|admin>')
        return
    target_id = int(args[0]) if args[0].isdigit() else None
    if target_id is None:
        await update.message.reply_text('Невірний Telegram ID.')
        return
    if not update_user_role_status(target_id, args[1], 'active'):
        await update.message.reply_text('Користувача не знайдено. Нехай надішле /start.')
        return
    await update.message.reply_text(f'Роль користувача {target_id} змінено на {args[1]}.')
    log_event(user.id, 'promote', f'target={target_id} role={args[1]}')


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin_user(user.id):
        await update.message.reply_text('Тільки адміністратор може заблокувати користувача.')
        return
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Використання: /ban <telegram_id>')
        return
    target_id = int(args[0]) if args[0].isdigit() else None
    if target_id is None:
        await update.message.reply_text('Невірний Telegram ID.')
        return
    if not update_user_role_status(target_id, 'guest', 'banned'):
        await update.message.reply_text('Користувача не знайдено. Нехай надішле /start.')
        return
    await update.message.reply_text(f'Користувача {target_id} заблоковано.')
    log_event(user.id, 'ban', f'target={target_id}')


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin_user(user.id):
        await update.message.reply_text('Тільки адміністратор може надсилати розсилки.')
        return
    text = ' '.join(context.args).strip()
    if not text:
        await update.message.reply_text('Використання: /broadcast <повідомлення>')
        return
    users = list_users()
    count = 0
    for profile in users:
        if profile['status'] == 'active' and profile['role'] != 'banned':
            try:
                await context.bot.send_message(chat_id=profile['telegram_id'], text=f'📢 Адміністрація: {text}')
                count += 1
            except Exception:
                pass
    await update.message.reply_text(f'Повідомлення надіслано {count} користувачам.')
    log_event(user.id, 'broadcast', f'count={count}')


async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return

    user_text = update.message.text
    if user_text == '📋 Меню':
        menu_message = (
            '📋 <b>Меню команд</b>\n\n'
            '/bitcoin - ціна Bitcoin (BTC)\n'
            '/ethereum - ціна Ethereum (ETH)\n'
            '/solana - ціна Solana (SOL)\n'
            '/all - ціни всіх трьох криптовалют\n'
            '/growth 1h - Топ 10 ріст за 1 годину\n'
            '/growth 24h - Топ 10 ріст за 24 години\n'
            '/growth 7d - Топ 10 ріст за 7 днів\n\n'
            'Джерело даних: CoinMarketCap API.\n'
            'Введіть команду або натисніть кнопку нижче.'
        )
        await update.message.reply_text(menu_message, parse_mode='HTML', reply_markup=get_main_keyboard())
        return

    if user_text == '📈 Ріст':
        growth_message = (
            '📈 <b>Показники росту</b>\n\n'
            '/growth 1h - Топ 10 ріст за 1 годину\n'
            '/growth 24h - Топ 10 ріст за 24 години\n'
            '/growth 7d - Топ 10 ріст за 7 днів\n\n'
            'Введіть команду або натисніть один із варіантів.'
        )
        await update.message.reply_text(growth_message, parse_mode='HTML', reply_markup=get_main_keyboard())
        return

    if user_text == '❓ Довідка':
        help_message = (
            '📚 <b>Як користуватися ботом:</b>\n\n'
            '/bitcoin - ціна Bitcoin (BTC)\n'
            '/ethereum - ціна Ethereum (ETH)\n'
            '/solana - ціна Solana (SOL)\n'
            '/all - показати ціни всіх трьох криптовалют\n\n'
            '/start - показати привіт\n'
            '/help - показати довідку\n\n'
            'Інформація оновлюється в реальному часі з CoinMarketCap API.'
        )
        await update.message.reply_text(help_message, parse_mode='HTML', reply_markup=get_main_keyboard())
        return

    await update.message.reply_text(
        'Я розумію лише команди. Скористайтеся /help для списку доступних команд.',
        reply_markup=get_main_keyboard()
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Error: {context.error}')
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('Виникла помилка. Спробуйте ще раз пізніше.')


def build_bot_application() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('myrole', myrole_command))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('request', request_command))
    application.add_handler(CommandHandler('adminpanel', adminpanel_command))
    application.add_handler(CommandHandler('promote', promote_command))
    application.add_handler(CommandHandler('ban', ban_command))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(CommandHandler('bitcoin', bitcoin_command))
    application.add_handler(CommandHandler('ethereum', ethereum_command))
    application.add_handler(CommandHandler('solana', solana_command))
    application.add_handler(CommandHandler('all', all_command))
    application.add_handler(CommandHandler('growth', growth_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press))
    application.add_error_handler(error_handler)
    return application


if __name__ == '__main__':
    init_db()
    application = build_bot_application()
    print('Запуск Telegram бота...')
    application.run_polling()
