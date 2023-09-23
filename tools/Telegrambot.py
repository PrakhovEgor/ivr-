import telebot
import json
import time
import datetime

bot = telebot.TeleBot('6162063865:AAEEuoQt4p_HjdUyKSN0M-eQbo48IiR84sc')


@bot.message_handler(commands=['start'])
def start_message(message):
    print(message.chat.id)


while True:
    with open("../static/tg_data.json", 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        data = file_data["data"]

        new_data = []

        for item in data:
            if datetime.datetime.strptime(item["start_date"], "%Y-%m-%dT%H:%M") <= datetime.datetime.now():
                for acc in item["tg_id"]:
                    bot.send_message(acc, item["plants"])
                new_item = item

                counts, typed = new_item['period'].split("_")
                if counts != "0":
                    if typed == "hour":
                        new_item['start_date'] = datetime.datetime.strptime(new_item["start_date"], "%Y-%m-%dT%H:%M") + datetime.timedelta(hours=int(counts))
                    elif typed == "day":
                        new_item['start_date'] = datetime.datetime.strptime(new_item["start_date"], "%Y-%m-%dT%H:%M") + datetime.timedelta(days=int(counts))
                    elif typed == "month":
                        new_item['start_date'] = datetime.datetime.strptime(new_item["start_date"], "%Y-%m-%dT%H:%M") + datetime.timedelta(months=int(counts))
                    elif typed == "year":
                        new_item['start_date'] = datetime.datetime.strptime(new_item["start_date"], "%Y-%m-%dT%H:%M") + datetime.timedelta(years=int(counts))
                    new_item['start_date'] = new_item['start_date'].strftime("%Y-%m-%dT%H:%M")
                    new_data.append(new_item)
                    print(new_item)
            else:
                new_data.append(item)
                print("Рано")

        file_data["data"] = new_data
        file.seek(0)
        file.truncate()
        json.dump(file_data, file, indent=2)
    time.sleep(10)






