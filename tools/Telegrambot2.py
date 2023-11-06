import telebot
import json
import time
import requests

bot = telebot.TeleBot('6515349176:AAEOpCVm_bJhXW2rAYZ3OtAwNUtggau3pEE')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
                     "Для того, чтобы зарегистрировать аккаунт введите Ваши данные от сайта: Почту и пароль через запятую.")


@bot.message_handler(content_types='text')
def message_reply(message):
    try:
        if len(message.text.split(',')) != 2:
            bot.send_message(message.chat.id, "Неправильный формат ввода. Пример правильного: 1@1.com, my_password")
        else:
            email, password = message.text.split(',')
            email = email.strip()
            password = password.strip()
            data = requests.get("http://127.0.0.1:5000/todo/api/v1.0/emails").json()['data'][0]
            if email in data.keys():
                if str(data[email]) != str(password):
                    bot.send_message(message.chat.id, "Неверный пароль")
                else:
                    if [message.chat.id] in requests.get("http://127.0.0.1:5000/todo/api/v1.0/tg_accs").json()[
                        'tg_accs']:
                        bot.send_message(message.chat.id, "Ваш аккаунт уже зарегистрирован!")
                    else:
                        requests.post("http://127.0.0.1:5000/todo/api/v1.0/tg_registration",
                                      json={"tg_data": [email, message.chat.id, message.chat.username]})
                        bot.send_message(message.chat.id,
                                         "Ваш аккаунт успешно зарегистрирован! Так же Вы можете зарегестрировать несколько аккаунтов")
            else:
                bot.send_message(message.chat.id, "Пользователь с данной почтой не найден")
    except:
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже")


bot.infinity_polling()
