import datetime
import json


class Plants:
    def __init__(self, id=None, email=None, mysql=None):
        self.id = id
        self.email = email
        self.mysql = mysql

    def get_user_plants_id(self):
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT plant_id FROM user_data WHERE user_id = {self.id} AND m_type='own'")
        res = cur.fetchall()
        cur.close()
        return [x[0] for x in res]

    def get_plants_idname(self, search='', id=None, img=False, include_users=False, include_date=False):
        where_clause = ''
        if include_users:
            id = id or self.get_user_plants_id()
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
            # return [[plant[0], plant[1], plant[2]] for plant in new_plants]
        if img:
            new_res = []
            for i in res:
                i = list(i)
                img_path = i[1] + '.jpg' if i[3] is None or i[3] == 0 else f'{self.email}/{i[1]}.jpg'
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

    def save_plants_to_user(self, plants_ids):
        cursor = self.mysql.connection.cursor()
        for id in plants_ids:
            cursor.execute(f" INSERT INTO user_data(user_id, plant_id, m_type, date) VALUES(%s, %s, %s, %s)",
                           (self.id, id, "own", datetime.datetime.now().date()))
            self.mysql.connection.commit()
        cursor.close()
        return

    def get_id_by_plantname(self, name):
        cur = self.mysql.connection.cursor()
        cur.execute("SELECT id FROM plants WHERE plant_name = %s", [name])
        res = cur.fetchall()
        cur.close()
        return res[0]

    def save_custom_plant(self, name, d):
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
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT plant_name, custom FROM plants")
        res = cur.fetchall()
        cur.close()
        res = [x[0] for x in res if x[1] in [None, 0, int(include_users)]]
        return res

    def get_user_plants_adds(self):
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT plant_id, addition FROM user_data WHERE user_id = {self.id} AND m_type='addition'")
        res = cur.fetchall()
        cur.close()

        return dict(res)


    def get_plant_history(self, plant_id, m_type='all'):
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

        d = {
            'watering': 'Полив',
            'harvesting': 'Сбор урожая',
            'planting_seeds': 'Посев семян',
            'planting_sprouts': 'Посадка ростков',
            'tending_weeding': 'Прополка',
            'tending_fertilizing': 'Внесение удобрений',
            'tending_pest_control': 'Борьба с вредителями',
            'tending_transplant': 'Пересадка',
            'tending_pruning': 'Подрезка'
        }

        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT * FROM user_data WHERE user_id = {self.id} AND plant_id={plant_id} AND m_type IN {tuple(avail)}")
        res = cur.fetchall()
        cur.close()
        res = [list(x) for x in res]

        for i in range(len(res)):
            res[i][-3] = json.loads(res[i][-3])
            res[i][2] = d.get(res[i][2])
        return res

    def get_user_tg(self, id=False):
        email = self.email
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT name{', telegram_id' * int(id)} FROM telegram_data WHERE email = %s", [email])
        res = cur.fetchall()
        cur.close()
        return res



