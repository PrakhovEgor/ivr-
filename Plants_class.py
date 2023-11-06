import datetime
import json
import os


class Plants:
    def __init__(self, id=None, email=None, mysql=None):
        self.id = id
        self.email = email
        self.mysql = mysql

    def get_user_plants_id(self):  # Возвращает id растений юзера
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT plant_id FROM user_data WHERE user_id = {self.id} AND m_type='own'")
        res = cur.fetchall()
        cur.close()
        return [x[0] for x in res]

    def get_plants_idname(self, search='', id=None, img=False, include_users=False, include_date=False):
        """
        :param search: фильтр на название
        :param id: id растений(ия)
        :param img: Добавить ли ссылку на фото?
        :param include_users: Добавить ли пользовательские растения?
        :param include_date: Добавить дату?
        :return: Список с id, name, desctiprion, img?, date? для каждого растения
        """
        where_clause = ''
        if include_users:
            if id == None:
                id = self.get_user_plants_id()
            else:
                id = set(id) | set(self.get_user_plants_id())
        else:
            where_clause = "WHERE custom IS NULL"
        if id is None:
            query = ""
        elif len(id) == 0:
            return []
        elif type(id) == int or type(id) == str:
            query = f'WHERE id = {id}'
            where_clause = ""

        elif len(id) == 1:
            if type(id) == set:
                id = id.pop()
            elif type(id) == list:
                id = id[0]

            query = f'WHERE id = {id}'
            where_clause = ""
        else:
            id_tuple = tuple(id)
            query = f'WHERE id IN {id_tuple}'
            where_clause = ""

        sql_query = f"SELECT * FROM plants {query}{where_clause}"
        cur = self.mysql.connection.cursor()
        cur.execute(sql_query)
        res = cur.fetchall()
        cur.close()

        if search:
            new_plants = [plant for plant in res if search.strip().lower() in plant[1].strip().lower()]
            res = new_plants.copy()
        if img:
            new_res = []
            for i in res:
                i = list(i)
                img_path = ""
                if i[1] + ".jpg" in os.listdir('static/' + self.email):
                    img_path = f'{self.email}/{i[1]}.jpg'
                elif i[3] is None or i[3] == 0:
                    img_path = i[1] + '.jpg'
                else:
                    img_path = f'{self.email}/{i[1]}.jpg'
                if not os.path.exists("static/" + img_path):
                    img_path = "image_placeholder.jpg"
                new_res.append(i + [img_path])
            res = new_res.copy()
        if include_date:
            sql_query = f"SELECT * FROM user_data WHERE user_id = {self.id} AND m_type='own'"
            cur = self.mysql.connection.cursor()
            cur.execute(sql_query)
            temp = cur.fetchall()
            cur.close()
            d = {}

            for i in temp:
                d[i[1]] = i[4]
            for i in range(len(res)):
                res[i].append(d[res[i][0]])
        return res

    def save_plants_to_user(self, plants_ids):  # Сохраняет растение юзеру
        cursor = self.mysql.connection.cursor()
        for id in plants_ids:
            cursor.execute(f" INSERT INTO user_data(user_id, plant_id, m_type, date) VALUES(%s, %s, %s, %s)",
                           (self.id, id, "own", datetime.datetime.now().date()))
            self.mysql.connection.commit()
        cursor.close()
        return

    def get_id_by_plantname(self, name):  # Возвращает id растения по его названию
        cur = self.mysql.connection.cursor()
        cur.execute("SELECT id FROM plants WHERE plant_name = %s", [name])
        res = cur.fetchall()
        cur.close()
        return res[0]

    def save_custom_plant(self, name, d):  # Сохраняет кастомное растение юзера
        cursor = self.mysql.connection.cursor()
        cursor.execute("INSERT INTO plants(plant_name, description, custom) VALUES(%s, %s, %s)",
                       (name, json.dumps(d, ensure_ascii=False).encode('utf8'), True))
        self.mysql.connection.commit()
        cursor.close()

        cursor = self.mysql.connection.cursor()
        cursor.execute(f"INSERT INTO user_data(user_id, plant_id, m_type, date) VALUES(%s, %s, %s, %s)",
                       (self.id, self.get_id_by_plantname(name), 'own', datetime.datetime.now().date()))
        self.mysql.connection.commit()
        cursor.close()
        return

    def get_all_plants_names(self, include_users=True):
        """
        :param include_users: брать ли растения пользователя?
        :return: Список всех названий растений
        """
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT plant_name, custom FROM plants")
        res = cur.fetchall()
        cur.close()
        res = [x[0] for x in res if x[1] in [None, 0, int(include_users)]]
        return res

    def get_plant_history(self, plant_id, m_type='all'):
        """
        :param plant_id: id растения
        :param m_type: тип действия
        :return: список действия по растению и действию
        """
        plant_id = plant_id
        if m_type == "all":
            avail = ['watering', 'harvesting', 'planting_seeds', 'planting_sprouts',
                     'tending_weeding', 'tending_fertilizing', 'tending_pest_control',
                     'tending_transplant', 'tending_pruning']
        elif m_type == "watering":
            avail = ['watering', 'watering']
        elif m_type == "planting":
            avail = ['planting_seeds', 'planting_sprouts']
        elif m_type == "tending":
            avail = ['tending_weeding', 'tending_fertilizing', 'tending_pest_control',
                     'tending_transplant', 'tending_pruning']
        elif m_type == "harvesting":
            avail = ['harvesting', 'harvesting']

        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT * FROM user_data WHERE user_id = {self.id} AND plant_id={plant_id} AND m_type IN {tuple(avail)}")
        res = cur.fetchall()
        cur.close()
        res = [list(x) for x in res]
        return res
