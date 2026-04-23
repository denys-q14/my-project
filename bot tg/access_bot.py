import threading

from access_bot_common import init_db, ADMIN_PANEL_HOST, ADMIN_PANEL_PORT
from access_bot_backend import build_bot_application
from access_bot_frontend import run_admin_panel


def main() -> None:
    init_db()
    threading.Thread(target=run_admin_panel, daemon=True).start()
    application = build_bot_application()
    print(f'Запуск адмін-панелі: http://{ADMIN_PANEL_HOST}:{ADMIN_PANEL_PORT}/admin')
    print('Запуск Telegram бота...')
    application.run_polling()


if __name__ == '__main__':
    main()
