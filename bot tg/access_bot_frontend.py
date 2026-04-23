import secrets
from flask import Flask, request, redirect, url_for, render_template_string, session

from access_bot_common import (
    ADMIN_PASSWORD,
    ADMIN_PANEL_HOST,
    ADMIN_PANEL_PORT,
    init_db,
    list_users,
    remove_user,
    update_user_role_status,
)

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

LOGIN_TEMPLATE = '''
<!doctype html>
<html lang="uk">
<head>
    <meta charset="utf-8">
    <title>Адмін-панель</title>
    <style>
        body { font-family: Arial, sans-serif; background:#f1f5f9; margin:0; padding:0; }
        .container { max-width:800px; margin:40px auto; padding:20px; background:white; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,0.1); }
        h1 { margin-top:0; }
        input[type=password] { width:100%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px; }
        button { padding:10px 20px; border:none; border-radius:5px; background:#2563eb; color:white; cursor:pointer; }
        .alert { color:#b91c1c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Вхід до адмін-панелі</h1>
        {% if error %}
            <p class="alert">{{ error }}</p>
        {% endif %}
        <form method="post">
            <label>Пароль адміністратора</label>
            <input type="password" name="password" placeholder="Введіть пароль" required>
            <button type="submit">Увійти</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!doctype html>
<html lang="uk">
<head>
    <meta charset="utf-8">
    <title>Адмін-панель</title>
    <style>
        body { font-family: Arial, sans-serif; background:#f5f7fb; margin:0; padding:0; }
        .container { max-width:1100px; margin:30px auto; padding:20px; background:white; border-radius:12px; box-shadow:0 4px 18px rgba(0,0,0,0.08); }
        h1 { margin-top:0; }
        table { width:100%; border-collapse:collapse; }
        th, td { padding:12px 10px; border-bottom:1px solid #e2e8f0; text-align:left; }
        th { background:#f8fafc; }
        .tag { display:inline-block; padding:4px 10px; border-radius:999px; background:#e2e8f0; }
        .tag.admin { background:#c7f9cc; }
        .tag.user { background:#dbeafe; }
        .tag.guest { background:#fef3c7; }
        .tag.banned { background:#fecaca; }
        form { display:inline; }
        select, input[type=text] { padding:6px 8px; margin-right:6px; border:1px solid #cbd5e1; border-radius:6px; }
        button { padding:8px 12px; border:none; border-radius:7px; cursor:pointer; background:#2563eb; color:white; }
        button.small { padding:6px 10px; }
        .danger { background:#dc2626; }
        .message { margin:10px 0; padding:10px; border-radius:8px; background:#d1fae5; color:#065f46; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Адмін-панель бота</h1>
        <p>Адреса панелі: <b>{{ panel_url }}</b></p>
        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}
        <p>Зарегістровані користувачі: <b>{{ users|length }}</b></p>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Telegram</th>
                    <th>Ім'я</th>
                    <th>Роль</th>
                    <th>Статус</th>
                    <th>Оновлено</th>
                    <th>Дії</th>
                </tr>
            </thead>
            <tbody>
            {% for user in users %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.telegram_id }}</td>
                    <td>{{ user.username or user.first_name or '—' }}</td>
                    <td><span class="tag {{ user.role }}">{{ user.role }}</span></td>
                    <td>{{ user.status }}</td>
                    <td>{{ user.updated_at }}</td>
                    <td>
                        <form method="post" action="{{ url_for('update_user_role') }}">
                            <input type="hidden" name="telegram_id" value="{{ user.telegram_id }}">
                            <select name="role">
                                <option value="guest" {% if user.role == 'guest' %}selected{% endif %}>guest</option>
                                <option value="user" {% if user.role == 'user' %}selected{% endif %}>user</option>
                                <option value="admin" {% if user.role == 'admin' %}selected{% endif %}>admin</option>
                            </select>
                            <select name="status">
                                <option value="active" {% if user.status == 'active' %}selected{% endif %}>active</option>
                                <option value="pending" {% if user.status == 'pending' %}selected{% endif %}>pending</option>
                                <option value="banned" {% if user.status == 'banned' %}selected{% endif %}>banned</option>
                            </select>
                            <button class="small" type="submit">Оновити</button>
                        </form>
                        <form method="post" action="{{ url_for('remove_user') }}" style="margin-top:4px;">
                            <input type="hidden" name="telegram_id" value="{{ user.telegram_id }}">
                            <button class="small danger" type="submit">Видалити</button>
                        </form>
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
        <p><a href="{{ url_for('logout') }}">Вийти</a></p>
    </div>
</body>
</html>
'''


@app.route('/login', methods=['GET', 'POST'])
def login() -> str:
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session['admin_authenticated'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Невірний пароль. Спробуйте ще раз.'
    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route('/logout')
def logout() -> str:
    session.pop('admin_authenticated', None)
    return redirect(url_for('login'))


@app.route('/admin')
def admin_dashboard() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    users = list_users()
    panel_url = f'http://{ADMIN_PANEL_HOST}:{ADMIN_PANEL_PORT}/admin'
    message = request.args.get('message')
    return render_template_string(ADMIN_TEMPLATE, users=users, panel_url=panel_url, message=message)


@app.route('/admin/update', methods=['POST'])
def update_user_role() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    telegram_id = request.form.get('telegram_id')
    role = request.form.get('role')
    status = request.form.get('status')
    if not telegram_id or not telegram_id.isdigit() or role not in ('guest', 'user', 'admin') or status not in ('active', 'pending', 'banned'):
        return redirect(url_for('admin_dashboard', message='Невірні дані.'))
    update_user_role_status(int(telegram_id), role, status)
    return redirect(url_for('admin_dashboard', message='Роль користувача оновлено.'))


@app.route('/admin/remove', methods=['POST'])
def remove_user() -> str:
    if not session.get('admin_authenticated'):
        return redirect(url_for('login'))
    telegram_id = request.form.get('telegram_id')
    if telegram_id and telegram_id.isdigit():
        remove_user(int(telegram_id))
    return redirect(url_for('admin_dashboard', message='Користувача видалено.'))


def run_admin_panel() -> None:
    init_db()
    app.run(host=ADMIN_PANEL_HOST, port=ADMIN_PANEL_PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    run_admin_panel()
