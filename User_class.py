import datetime
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import session
from dateutil.parser import parse


class User:
    def __init__(self, id=None, email=None, mysql=None):
        self.id = id
        self.email = email
        self.mysql = mysql

    def get_user_password(self, email):  # Возвращает пароль по почте
        cur = self.mysql.connection.cursor()
        cur.execute("SELECT password FROM auth_data WHERE email=%s", [email])
        res = cur.fetchall()
        cur.close()
        return res[0][0]

    def send_email(self, receiver_email, subject, body):  # Отправляет письмо
        sender_email = 'garden-help@inbox.ru'
        sender_password = 'mfm4cSmWiuca6WQegwkb'
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, _charset='utf-16'))
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return

    def update_password(self, email, password):  # Обновляет пароль на новый
        cur = self.mysql.connection.cursor()
        cur.execute("UPDATE auth_data SET password=%s WHERE email=%s", [password, email])
        self.mysql.connection.commit()
        cur.close()
        return

    def save_user(self, email, password):  # Сохраняет юзера
        cursor = self.mysql.connection.cursor()
        cursor.execute(' INSERT INTO auth_data(email, password) VALUES(%s,%s)', (email, password))
        self.mysql.connection.commit()
        cursor.close()

        cursor = self.mysql.connection.cursor()
        cursor.execute(
            f" CREATE TABLE `{self.get_id_by_email(email)}` (`id` INT NOT NULL AUTO_INCREMENT , `plant_id` INT NOT NULL , `m_type` TEXT NULL , `count` INT NULL , `weight` FLOAT NULL, `addition` TEXT NULL , `date` DATE NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;")
        self.mysql.connection.commit()
        cursor.close()

    def get_id_by_email(self, email):  # Возвращает id юзера по почте
        cur = self.mysql.connection.cursor()
        cur.execute("SELECT id FROM auth_data WHERE email=%s", [email])
        res = cur.fetchall()
        cur.close()
        return str(res[0][0])

    def get_date_list(self, start, end):  # Возвращает список дат
        if type(start) == str:
            start = self.parse_date_string(start)
        if type(end) == str:
            end = self.parse_date_string(end)
        date_list = []
        id = 1
        if start <= end:
            while start <= end:
                date_list.append([id, start])
                start += datetime.timedelta(days=1)
                id += 1
        else:
            for i in range(7):
                date_list.append([id, start])
                start += datetime.timedelta(days=1)
                id += 1

        actions = self.get_user_actions(date_list[0], date_list[-1])
        temp = []
        for day_t in date_list:
            day = day_t.copy()
            if type(day_t[1]) != datetime.date:
                day[1] = day_t[1].date()
            watering_count = 0
            planting_count = 0
            harvesting_count = 0
            tending_count = 0
            for action in actions:
                if day[1] == action[2] and action[1] == "watering":
                    watering_count += 1
                elif day[1] == action[2] and action[1].startswith("planting"):
                    planting_count += 1
                elif day[1] == action[2] and action[1] == "harvesting":
                    harvesting_count += 1
                elif day[1] == action[2] and action[1].startswith("tending"):
                    tending_count += 1

            temp.append([day[0], day[1], watering_count, planting_count, harvesting_count, tending_count])

        date_list = temp

        return date_list

    def get_user_actions(self, start_date, end_date):
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT plant_id, m_type, date FROM `{self.id}` WHERE date >= '{start_date[1]}' AND date <= '{end_date[1]}'")
        res = cur.fetchall()
        cur.close()
        return res

    def save_action(self, plants_lst, type_act):
        cursor = self.mysql.connection.cursor()
        for i in plants_lst:
            cursor.execute(
                f" INSERT INTO `{self.id}`(plant_id, m_type, date, count, weight) VALUES(%s, %s, %s, %s, %s)",
                (i[0], type_act, self.parse_date_string(session.get("date_to_edit")), i[1], i[2]))
            self.mysql.connection.commit()
        cursor.close()
        return

    def get_user_plants_adds(self):
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT plant_id, addition FROM `{self.id}` WHERE m_type='addition'")
        res = cur.fetchall()
        cur.close()

        return dict(res)

    def save_custom_adds(self, plant_id, d):
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"INSERT INTO `{self.id}`(plant_id, m_type, addition) VALUES(%s, %s, %s)",
            (plant_id, 'addition', d))
        self.mysql.connection.commit()
        cur.close()
        return

    def delete_plant_from_user(self, plant_id, name, m_type=False):
        if m_type:
            cur = self.mysql.connection.cursor()
            cur.execute(
                f"DELETE FROM `{session.get('id')}` WHERE plant_id={plant_id} AND m_type='addition'")
            self.mysql.connection.commit()
            cur.close()
        else:
            cur = self.mysql.connection.cursor()
            cur.execute(f"DELETE FROM `{session.get('id')}` WHERE plant_id={plant_id}")
            self.mysql.connection.commit()
            cur.close()

        if os.path.isdir('static/' + session.get('email')) and name + '.jpg' in os.listdir(f"static/{session.get('email')}"):
            os.remove(os.path.join(f"static/{session.get('email')}", name + '.jpg'))
        return

    def get_user_tg(self, id=False):
        email = self.email
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT name{', telegram_id' * int(id)} FROM telegram_data WHERE email = %s", [email])
        res = cur.fetchall()
        cur.close()
        return res

    def parse_date_string(self, date_string):
        try:
            parsed_date = parse(date_string)
            return parsed_date
        except TypeError:
            return date_string

    def save_bed(self, data):
        name = data['name']
        data_id = data['id']
        print('id', data_id)
        if not data_id:
            cur = self.mysql.connection.cursor()
            cur.execute(
                "INSERT INTO garden_beds(`user_id`, `name`, `data`) VALUES(%s, %s, %s)",
                (self.id, name, json.dumps(data)))
            self.mysql.connection.commit()
            cur.close()
        else:
            data_id = data['id']
            data = json.dumps(data)
            print(data_id, self.id, name, data)
            cur = self.mysql.connection.cursor()
            cur.execute(f"UPDATE garden_beds SET user_id = %s, name = %s, data = %s WHERE id = %s",
                        [self.id, name, data, data_id]
                        )

            self.mysql.connection.commit()
            cur.close()
            print('success')
        return

    def get_beds(self, id=None):
        query = ''
        if id:
            query = f"AND id = {id}"
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT * FROM garden_beds WHERE user_id = %s {query}", [self.id])
        res = cur.fetchall()
        cur.close()
        print(res)
        return res

    def delete_bed(self, id):
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"DELETE FROM garden_beds WHERE id={id}")
        self.mysql.connection.commit()
        cur.close()
        return
