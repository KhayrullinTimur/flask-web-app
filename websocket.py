from flask import Blueprint, render_template
from flask_socketio import SocketIO, emit

# Создаем Blueprint для WebSocket подприложения
websocket_bp = Blueprint('websocket', __name__)
socketio = SocketIO()

# Определяем событие 'message'
@socketio.on('message')
def handle_message(message):
    # Обрабатываем полученное сообщение
    # В данном примере мы просто отправляем обратно тоже сообщение
    emit('message', message)

# Регистрируем WebSocket подприложение
def register_websocket(app):
    socketio.init_app(app)
    app.register_blueprint(websocket_bp)

