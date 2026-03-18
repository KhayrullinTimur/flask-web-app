import pytest
from models import Product, User

# Тест модели Product
def test_product_model():
    # Создаем объект Product
    product = Product(name='Test Product', price=10.99)

    # Проверяем, что атрибуты модели установлены корректно
    assert product.name == 'Test Product'
    assert product.price == 10.99


# Тест модели User
def test_user_model():
    # Создаем объект User
    user = User(username='testuser', email='test@example.com')

    # Проверяем, что атрибуты модели установлены корректно
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'


# Запускаем тесты
if __name__ == '__main__':
    pytest.main()