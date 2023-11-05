import unittest

from bs4 import BeautifulSoup

from main import app, transform_period


class TestApp(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_home_status_code(self):
        response = self.app.get('/', follow_redirects=True)  # Должен перенаправить на страницу авторизации
        self.assertEqual(response.status_code, 200)

    def test_login_status_code(self):
        response = self.app.get('/login', follow_redirects=True)  # Должен перенаправить на страницу авторизации
        self.assertEqual(response.status_code, 200)

    def test_register_contains_element(self):
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Используем BeautifulSoup для разбора HTML-кода страницы
        soup = BeautifulSoup(response.data, 'html.parser')

        # Проверяем наличие элемента с определенным CSS классом (например, 'my-component')
        element = soup.find(class_='link-success')
        self.assertIsNotNone(element)

    def test_transform_period(self):
        corr_input = [{'id': 2, 'email': 'egor.prakhov@mail.ru', 'name': 'Напоминание', 'm_type': '-', 'tg_id': ['1'], 'plants': [], 'start_date': '2023-11-06T22:00', 'period': '1_day', 'comment': '', 'plants_ids': []}]
        corr_output = [{'id': 2, 'email': 'egor.prakhov@mail.ru', 'name': 'Напоминание', 'm_type': '-', 'tg_id': ['1'], 'plants': [], 'start_date': '2023-11-06T22:00', 'period': 'каждый день', 'comment': '', 'plants_ids': []}]

        test_output = transform_period(corr_input)
        self.assertEqual(corr_output, test_output)

if __name__ == '__main__':
    unittest.main()