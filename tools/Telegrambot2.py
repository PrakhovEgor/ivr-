import telebot
import json
import time
import requests

bot = telebot.TeleBot('6162063865:AAEEuoQt4p_HjdUyKSN0M-eQbo48IiR84sc')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Введите почту, с которой Вы регистрировались на сайте")



@bot.message_handler(content_types='text')
def message_reply(message):
    try:
        if [message.text.strip()] in requests.get("http://127.0.0.1:5000/todo/api/v1.0/emails").json()['emails']:
            if [message.text.strip()] in requests.get("http://127.0.0.1:5000/todo/api/v1.0/tg_emails").json()['emails']:
                bot.send_message(message.chat.id, "Ваш аккаунт уже зарегистрирован!")
            else:
                bot.send_message(message.chat.id, "Ваш аккаунт успешно зарегистрирован!")
                requests.post("http://127.0.0.1:5000/todo/api/v1.0/tg_registration", json={"tg_data": [message.text.strip(), message.chat.id, message.chat.username]})
        else:
            bot.send_message(message.chat.id, "Пользователь с данной почтой не найден")
    except:
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже")


bot.polling()