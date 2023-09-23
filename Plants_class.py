
import json


class Plants:
    def __init__(self, id=None, email=None, mysql=None):
        self.id = id
        self.email = email
        self.mysql = mysql

    def get_user_plants_id(self):
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT plant_id FROM `{self.id}` WHERE m_type='own'")
        res = cur.fetchall()
        cur.close()
        return [x[0] for x in res]

    def get_plants_idname(self, search='', id=None, img=False):
        if id == None:
            query = ""
        elif len(id) == 0:
            return []
        elif len(id) == 1:
            if type(id) == set:
                id = id.pop()
            elif type(id) == list:
                id = id[0]
            query = 'WHERE id = ' + str(id)
        else:
            query = 'WHERE id IN ' + str(tuple(id))
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT * FROM plants {query}")
        res = cur.fetchall()
        cur.close()
        if search != '':
            new_plants = []
            for plant in res:
                if search.strip().lower() in plant[1].strip().lower():
                    new_plants.append([plant[0], plant[1], plant[2]])
            return new_plants
        elif img == True:
            new_res = []
            for i in res:
                i = list(i)
                if i[3] == None or i[3] == 0:
                    new_res.append(i[:3] + [i[1] + '.jpg'])
                else:
                    new_res.append(i[:3] + [self.email + '/' + i[1] + '.jpg'])
            return new_res
        return res

    def save_plants_to_user(self, plants_ids):
        cursor = self.mysql.connection.cursor()
        for id in plants_ids:
            cursor.execute(f" INSERT INTO `{self.id}`(plant_id, m_type) VALUES(%s,%s)",
                           (id, "own"))
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
        cursor.execute(f"INSERT INTO `{self.id}`(plant_id, m_type) VALUES(%s, %s)",
                       (self.get_id_by_plantname(name), 'own'))
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

    def get_plant_history(self, plant_id):
        avail = ['watering', 'harvesting', 'planting',
                 'tending_weeding', 'tending_fertilizing', 'tending_pest_control',
                 'tending_transplant', 'tending_pruning']
        cur = self.mysql.connection.cursor()
        cur.execute(
            f"SELECT * FROM `{self.id}` WHERE plant_id={plant_id} AND m_type IN {tuple(avail)}")
        res = cur.fetchall()
        cur.close()

        return res

    def get_user_tg(self, id=False):
        email = self.email
        cur = self.mysql.connection.cursor()
        cur.execute(f"SELECT name{', telegram_id' * int(id)} FROM telegram_data WHERE email = %s", [email])
        res = cur.fetchall()
        cur.close()
        return res
