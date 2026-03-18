from flask import Flask, render_template, request, session, redirect, url_for, flash, request, jsonify
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_oauthlib.client import OAuth
from flask_socketio import SocketIO, emit
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash
from websocket import register_websocket
import os

# basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
register_websocket(app)
oauth = OAuth(app)
app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)


from models import Product, User

app.app_context().push()

@app.route('/')
def index():
    if is_logged_in():
        user_id = session['user_id']
        user = User.query.filter_by(id=user_id).first() # получаем первый продукт, принадлежащий определенному пользователю.
        if user is not None:
            username = user.username
            products = Product.query.filter_by(user_id=user_id).all()   # выпроняем запрос к базе данных, чтобы получить все продукты, принадлежащие определенному пользователю.
        else:
            # Обработка случая, когда пользователь не найден
            username = None
            products = []
        return render_template('index.html', is_logged_in=True, username=username, user_id=user_id, products=products)
    else:
        products = []
        return render_template('index.html', is_logged_in=False, products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """
    Функция для добавления нового продукта.

    :param name: Название продукта.
    :param price: Цена продукта. Не может быть отрицательной
    :return: Страница добавления продукта.
    """

    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        # description = request.form['description']
        price = float(request.form['price'])
        user_id = session['user_id']  # Получение user_id из сессии
        if price <= 0:
            flash('Цена должна быть положительным числом', 'error')
            return redirect(url_for('add_product'))
        product = Product(name=name, price=price, user_id=session['user_id'])

        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """
    Функция для редактирования продукта.

    :param name: Название продукта.
    :param price: Цена продукта. Не может быть отрицательной
    :return: Страница редактирования продукта.
    """

    if not is_logged_in():
        return redirect(url_for('login'))

    user_id = session['user_id']
    product = Product.query.get(product_id)

    if product is None or product.user_id != user_id:
        return redirect(url_for('index'))

    if request.method == 'POST':
        product.name = request.form['name']
        # product.description = request.form['description']
        product.price = request.form['price']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    """
    Функция для удаления продукта.

    args: product_id
    return: Страница удаления продукта
    """
    
    if not is_logged_in():
        return redirect(url_for('login'))

    product = Product.query.get(product_id)

    # Проверяем, существует ли продукт с указанным айди
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))

    # Проверяем, является ли текущий пользователь создателем продукта
    if product.user_id != session['user_id']:
        flash('You are not authorized to delete this product', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()
        flash('Product successfully deleted', 'success')
        return redirect(url_for('index'))

    return render_template('delete_product.html', product=product)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Регистрируем нового пользователя

    GET-параметры:
        Отсутствуют.

    POST-параметры:
        - email (строка): Адрес электронной почты нового пользователя.
        - username (строка): Имя нового пользователя.
        - password (строка): Пароль нового пользователя.
        - confirm_password (строка): Подтверждение пароля.

    :return: Перенаправление на страницу входа в случае успешной регистрации, иначе возвращает страницу регистрации с сообщением об ошибке.
    """
    
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        # Проверка существует ли пользователь с указанным именем или адресом электронной почты
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if existing_user:
            # return 'Username already exists'
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        if existing_email:
            flash('Email already exists')
            return redirect(url_for('register'))

        # Создание нового пользователя и сохранение в бд
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Регистрируем нового пользователя

    GET-параметры:
        Отсутствуют.

    POST-параметры:
        - username (строка): Имя нового пользователя.
        - password (строка): Пароль нового пользователя.

    :return: Перенаправление на страницу входа
    """

    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash('Invalid username or password', 'error')
        return render_template('login.html')

    return render_template('login.html')

def is_logged_in():
    return 'user_id' in session

@app.route('/logout')
def logout():
    """
    Выход из аккаунта
    """
    session.clear()
    return redirect(url_for('index'))

@app.route('/account', methods=['GET', 'POST'])
def account():
    """
    Аккаунт пользователя
    Возможность редактирования информации пользователя

    Methods:
        GET: Отображает страницу аккаунта с текущими данными пользователя.
        POST: Обрабатывает отправленную форму с обновленными данными пользователя.

    Returns:
        Если метод GET, возвращает отрендеренный шаблон 'account.html' с данными пользователя.
        Если метод POST, перенаправляет пользователя на страницу аккаунта с сообщением об успешном обновлении данных.

    Returns:
        Если метод GET, возвращает 'account.html' с данными пользователя.
        Если метод POST, перенаправляет пользователя на страницу аккаунта с сообщением об успешном обновлении данных.
    """

    # Получение текущего пользователя
    user = get_current_user()

    if request.method == 'POST':
        # Обработка отправленной формы
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        # Обновление данных пользователя в базе данных
        update_user(user.id, new_username, new_email, new_password)

        flash('Account information updated successfully.', 'success')
        return redirect(url_for('account'))

    return render_template('account.html', user=user)

def get_current_user():
    # Проверяем, аутентифицирован ли пользователь
    if 'user_id' in session:
        # Получаем идентификатор пользователя из сеанса
        user_id = session['user_id']
        # Ваш код для получения пользователя из базы данных по идентификатору
        user = User.query.get(user_id)
        return user
    else:
        return None


def update_user(user_id, new_username, new_email, new_password):
    # Находим пользователя по его айди
    user = User.query.get(user_id)

    # Обновляем данные пользователя
    user.username = new_username
    user.email = new_email
    user.password = generate_password_hash(new_password)

    # Сохраняем изменения в базе данных
    db.session.commit()

@socketio.on('connect')
def handle_login():
    if is_logged_in():
        print('Client Connected')
        socketio.emit('status', 'Client Connected')
    else:
        pass

@socketio.on('disconnect')
def handle_logout():
    if is_logged_in():
        print('Client Disconnected')
        socketio.emit('status', 'Client Disconnected')
    else:
        pass

@app.route('/users', methods=['GET'])
def get_users():
    # Получаем список пользователей из базы данных
    users = User.query.all()

    # Создаем список для хранения данных пользователей
    user_list = []

    # Проход по каждому пользователю и добавление его данных в список
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        user_list.append(user_data)

    # Возвращаем список пользователей в формате JSON
    return jsonify(user_list), 200

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """
    Сбрасываем пароль

    POST-параметры:
        - email (строка): Адрес электронной почты нового пользователя.

    :return: Перенаправление на страницу сброса пароля

    """
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.generate_reset_token()
            reset_url = url_for('reset_password_confirm', token=token, _external=True)

            subject = 'Сброс пароля'
            sender = 'noreply@example.com'
            recipients = [user.email]

            message = Message(subject=subject, sender=sender, recipients=recipients)
            message.body = render_template('email/reset_password.txt', user=user, reset_url=reset_url)
            message.html = render_template('email/reset_password.html', user=user, reset_url=reset_url)

            mail.send(message)

            flash('Письмо с инструкциями по сбросу пароля отправлено на указанный адрес электронной почты.', 'success')
            return redirect(url_for('login'))

        flash('Пользователь с указанным адресом электронной почты не найден.', 'error')
        return redirect(url_for('reset_password'))

    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=False)
    socketio.run(app)

