import datetime
import json
import os
from PIL import Image
import pandas as pd

from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from forms.auth_form import LoginForm, RegisterForm, ForgotPassForm, ResetPassForm
from flask_mysqldb import MySQL
from flask_mail import Mail
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import random
import string
import locale
from dateutil.parser import parse
import logging.config
from werkzeug.utils import secure_filename
from collections import defaultdict
from User_class import User
from Plants_class import Plants

locale.setlocale(locale.LC_TIME, 'ru_RU')

log_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(log_config)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bf&*gyusdgf^Sggf78y5sj'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'main_data'

UPLOAD_FOLDER = '/static/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

mail = Mail(app)
mysql = MySQL(app)

plant_params = ['Местоположение', 'Размножение', 'Группа', 'Зимостойкость', 'Применение', 'Выращивание',
                'Требования к почве', 'Доп. информация']

en_to_ru = {
    'watering': 'Полив',
    'harvesting': 'Сбор урожая',
    'planting': 'Посев',
    'planting_seeds': 'Посев семян',
    'planting_sprouts': 'Посадка ростков',
    'tending': 'Уход',
    'tending_weeding': 'Прополка',
    'tending_fertilizing': 'Внесение удобрений',
    'tending_pest_control': 'Борьба с вредителями',
    'tending_transplant': 'Пересадка',
    'tending_pruning': 'Подрезка',
    '-': '-'
}


def User_():
    if session.get("User.user"):
        User_d = list(session.get("User.user").values())
        return User(id=User_d[0], email=User_d[1], mysql=mysql)
    else:
        return User(mysql=mysql)


def Plants_():
    User_d = list(session.get("User.plant").values())
    return Plants(id=User_d[0], email=User_d[1], mysql=mysql)


@app.route('/process', methods=['POST'])
def process():
    data = dict(request.form)
    User_().save_bed(data)
    return request.form


@app.route('/get_data/<id>', methods=['GET'])
def get_data(id):
    data = User_().get_beds(id)[0][3]
    return data


@app.route('/', methods=["POST", "GET"])
def main():
    if not session.get("email", False):
        return redirect("/login")
    if not session.get("date_changed", 0):
        cur_date = datetime.datetime.now().date()
        start_date = cur_date - datetime.timedelta(days=3)
        end_date = cur_date + datetime.timedelta(days=3)
        session["timefrom"] = start_date
        session["timeto"] = end_date
        session["date_changed"] = 1

    if request.method == "POST":
        if "date_picker" in request.form:
            start_date = datetime.datetime.strptime(request.form["timefrom"], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(request.form["timeto"], "%Y-%m-%d")

            session["date_changed"] = 1
            session["timefrom"] = start_date
            session["timeto"] = end_date

        elif "date_reset" in request.form:
            cur_date = datetime.datetime.now().date()
            start_date = cur_date - datetime.timedelta(days=3)
            end_date = cur_date + datetime.timedelta(days=3)
            session["timefrom"] = start_date
            session["timeto"] = end_date
        elif "watering" in request.form:
            return redirect(f"day_history/watering/{request.form['watering']}")
        elif "planting" in request.form:
            return redirect(f"day_history/planting/{request.form['planting']}")
        elif "tending" in request.form:
            return redirect(f"day_history/tending/{request.form['tending']}")
        elif "harvesting" in request.form:
            return redirect(f"day_history/harvesting/{request.form['harvesting']}")
        else:
            button_id = list(request.form.keys())[-1]
            session["date_to_edit"] = get_date_by_id(button_id, session.get("days_list"))
            return redirect(f"/edit/{session.get('email')}")

    days_list = User_().get_date_list(session.get("timefrom"), session.get("timeto"))
    session["days_list"] = days_list

    return render_template("index.html", main="Журнал", day_list=days_list,
                           time_from=parse_date_string(session.get("timefrom")),
                           time_to=parse_date_string(session.get("timeto")), user=session.get('email'))


@app.route('/day_history/<m_type>/<day>', methods=["POST", "GET"])
def day_history(m_type, day):
    d = {"watering": 1,
         "planting": 2,
         "tending": 3,
         "harvesting": 4}
    status = d[m_type]
    # m_type = m_type
    history = User_().get_day_history(day)

    if request.method == "POST":
        if "watering" in request.form:
            status = d['watering']
        elif "planting" in request.form:
            status = d['planting']
        elif "tending" in request.form:
            status = d['tending']
        elif "harvesting" in request.form:
            status = d['harvesting']

    history_2 = sort_by_m_type(history, status)
    for i in range(len(history_2)):
        history_2[i][3] = json.loads(history_2[i][3])

    return render_template("day_history.html", status=status, history=history_2)


@app.route('/edit/<user>', methods=["POST", "GET"])
def edit(user):
    if not session.get('status', 0):
        session['status'] = 0
    search = ""
    plant_input_placeholder = ""

    plants = Plants_().get_plants_idname(search)
    plants_to_plant = []
    if request.method == "POST":
        if "watering" in request.form:
            session['list_status'] = 0
            session['status'] = 1
        elif "planting" in request.form:
            session['list_status'] = 0
            session['status'] = 2
        elif "tending" in request.form:
            session['list_status'] = 0
            session['status'] = 3
        elif "harvesting" in request.form:
            session['list_status'] = 0
            session['status'] = 4

        elif "list_all" in request.form:
            session['list_status'] = 0
            plants = Plants_().get_plants_idname(search)
        elif "list_user" in request.form:
            session['list_status'] = 1
            plants = Plants_().get_plants_idname(search=search, include_users=True)

        elif "search" in request.form:
            search = request.form["plant_input"]
            plants = Plants_().get_plants_idname(search)
            plant_input_placeholder = search

        elif "save_w" in request.form:
            save_plants(request.form)
            for plant in get_id_from_request_form(request.form):
                User_().save_action(plant, "watering", {})
            return redirect("/")

        elif "continue_p" in request.form:
            plants, plants_to_plant = continue_act(plants)
            if session.get("list_status") == 1:
                plants = Plants_().get_plants_idname(search=search, include_users=True)

        elif "save_p" in request.form:
            save_plants(request.form)
            seeds = get_lst_of_type("seeds", request.form.items())
            sprouts = get_lst_of_type("sprouts", request.form.items())
            files = {}
            for k, v in request.files.items():
                name = v.filename
                if name != '':
                    if not os.path.exists(f"static/{session.get('email')}"):
                        os.makedirs(f"static/{session.get('email')}")
                    v.save(os.path.join(f"static/{session.get('email')}", name))
                    files[k.split('_')[1]] = f"static/{session.get('email')}/" + name
            for seed in seeds:
                User_().save_action(seed[0], "planting_seeds", {"count": seed[1], "img_src": files.get(seed[0], '')})
            for sprout in sprouts:
                User_().save_action(sprout[0], "planting_sprouts",
                                    {"count": sprout[1], "img_src": files.get(sprout[0], '')})
            return redirect("/")

        elif "continue_t" in request.form:
            plants, plants_to_plant = continue_act(plants)
            if session.get("list_status") == 1:
                plants = Plants_().get_plants_idname(search=search, include_users=True)

        elif "save_t" in request.form:
            save_plants(request.form)
            temp = []
            for k, v in request.form.items():
                id = k[:k.find('_')]
                if k.endswith('type'):
                    temp.append([id, v])
            files = {}
            for k, v in request.files.items():
                name = v.filename
                if name != '':
                    if not os.path.exists(f"static/{session.get('email')}"):
                        os.makedirs(f"static/{session.get('email')}")
                    v.save(os.path.join(f"static/{session.get('email')}", name))
                    files[k.split('_')[1]] = f"static/{session.get('email')}/" + name

            for el in temp:
                User_().save_action(el[0], "tending_" + el[1], {"img_src": files.get(el[0], '')})
            return redirect("/")

        elif "continue_h" in request.form:
            plants, plants_to_plant = continue_act(plants)
            if session.get("list_status") == 1:
                plants = Plants_().get_plants_idname(search=search, include_users=True)
        elif "save_h" in request.form:
            save_plants(request.form)
            temp = defaultdict(list)
            for k, v in request.form.items():
                id = k[:k.find('_')]
                if k.endswith('count'):
                    temp[id] = [v]
                elif k.endswith('weight'):
                    temp[id] = temp.get(id) + [v]
            temp = list(map(lambda x: [x[0]] + x[1], list(temp.items())))

            files = {}
            for k, v in request.files.items():
                name = v.filename
                if name != '':
                    if not os.path.exists(f"static/{session.get('email')}"):
                        os.makedirs(f"static/{session.get('email')}")
                    v.save(os.path.join(f"static/{session.get('email')}", name))
                    files[k.split('_')[1]] = f"static/{session.get('email')}/" + name

            for el in temp:
                User_().save_action(el[0], "harvesting",
                                    {"count": el[1], "weight": el[2], "img_src": files.get(el[0], '')})
            return redirect("/")
    try:
        plants.sort(key=lambda x: x[2], reverse=True)
    except:
        pass
    return render_template("edit.html", main="Журнал", status=session.get('status', 0), plants=plants,
                           plant_input_placeholder=plant_input_placeholder, list_status=session.get('list_status', 1),
                           plants_to_plant=plants_to_plant, user=session.get('email'))


@app.route('/register/', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    email_error = False
    space_error = False
    if request.method == "POST":
        if form.validate():
            email = form.email.data
            password = form.password.data
            if " " in password:
                space_error = True
            else:
                if email in get_emails():
                    email_error = True
                else:
                    User_().save_user(email, password)
                    return redirect("/login")

    password_error = []
    for key, m in form.errors.items():
        val = m
        if val == ['This field is required.']:
            val = ["Все поля обязательны к заполнению"]
        password_error.append({'field': key, 'messages': val})

    return render_template("register.html", main="Регистрация", form=form,
                           password_error=password_error,
                           email_error=email_error, space_error=space_error)


@app.route('/login/', methods=["POST", "GET"])
def login():
    form = LoginForm()
    email_error = False
    password_error = False
    if request.method == "POST":
        if form.validate():
            email = form.email.data
            password = form.password.data
            if email not in get_emails():
                email_error = True

            elif password != User(mysql=mysql).get_user_password(email):
                password_error = True
            else:
                session["email"] = email
                id = User(mysql=mysql).get_id_by_email(session.get('email'))
                session["id"] = id
                session["User.user"] = User(email, id).__dict__
                session["User.plant"] = Plants(email, id).__dict__
                return redirect("/")

    return render_template("login.html", main="Авторизация", form=form, password_error=password_error,
                           email_error=email_error)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPassForm()
    success_text = ''
    danger_text = ''
    if request.method == 'POST':
        email = request.form['email']
        if email in get_emails():
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            session['email'] = email
            session['token'] = token
            body = f'''Здавствуйте, для смены пароля перейдите по ссылке: http://127.0.0.1:5000/reset_password/{token}'''
            User_().send_email(email, "Смена пароля", body)
            success_text = 'Письмо выслано на почту. Если письмо не пришло, проверьте категорию "Спам"'
        else:
            danger_text = 'Почта не найдена или не авторизована на сайте'
    return render_template('forgot_password.html', main="Восстановление", form=form, success_text=success_text,
                           danger_text=danger_text)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPassForm()
    if token != session.get('token', 'not token'):
        return redirect("/login")
    if request.method == "POST":
        if form.validate():
            password = form.password.data
            User_().update_password(session.get('email'), password)
            return redirect("login")

    password_error = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
    return render_template("reset_password.html", main="Смена пароля", form=form,
                           password_error=password_error)


@app.route('/user_plants', methods=['GET', 'POST'])
def user_plants():
    user_plants = Plants_().get_plants_idname(include_users=True, img=True, include_date=True)
    if request.method == "POST":
        if "add" in request.form:
            return redirect("/add_plants")
        elif "alph" in request.form:
            if session.get("alph_dir", "down") == "down":
                session["alph_dir"] = "up"
                user_plants.sort(key=lambda x: x[1])
            else:
                session["alph_dir"] = "down"
                user_plants.sort(key=lambda x: x[1], reverse=True)
        elif "date" in request.form:
            if session.get("date_dir", "down") == "down":
                session["date_dir"] = "up"
                user_plants.sort(key=lambda x: x[-1])
            else:
                session["date_dir"] = "down"
                user_plants.sort(key=lambda x: x[-1], reverse=True)

    return render_template("user_plants.html", active_up="text-white", main="Журнал", user=session.get('email'),
                           user_plants=user_plants, alph_dir=session.get("alph_dir", "down"),
                           date_dir=session.get("date_dir", "down"))


@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    accs = User_().get_user_tg()
    if request.method == "POST":
        if "make" in request.form:
            return redirect('/make_reminder')
        else:
            for k, v in request.form.items():
                if k.startswith("delete"):
                    delete_reminder(k.split("_")[1])
    data = transform_period(get_reminders())
    for i in range(len(data)):
        data[i]["plants"] = [f"{j + 1}) {x}" for j, x in enumerate(data[i]["plants"])]
    ids = [x["id"] for x in data]

    return render_template("reminders.html", active_rm="text-white", main="Журнал", user=session.get('email'),
                           data=data, accs=accs, ids=ids)


@app.route('/make_reminder', methods=['GET', 'POST'])
def make_reminder():
    search = ''
    plant_input_placeholder = ''
    name_error = ''
    accs_error = ''

    if request.method == "POST":
        print(request.form)
        if "search" in request.form:
            search = request.form["plant_input"]
            plant_input_placeholder = search
        elif "save" in request.form:
            if request.form["name"] == "":
                name_error = "Введите название"
            elif "accounts" not in request.form:
                accs_error = "Должен быть хотя бы один получатель"
            else:
                save_reminder(request.form)
                return redirect("/reminders")

    plants = Plants_().get_plants_idname(include_users=True)
    accounts = User_().get_user_tg()
    return render_template("make_reminders.html", plants=plants, plant_input_placeholder=plant_input_placeholder,
                           cur_date=datetime.date.today(), cur_time=datetime.datetime.now().strftime("%H:%M"),
                           timedelta=datetime.timedelta(days=1), accounts=accounts, user=session.get('email'),
                           name_error=name_error, accs_error=accs_error)


# @app.route('/telegram', methods=['GET', 'POST'])
# def telegram():
#     accounts = User_().get_user_tg()
#
#     if request.method == "POST":
#         if "add" in request.form:
#             return redirect("/telegram_add")
#     return render_template("telegram.html", main="Журнал", user=session.get('email'),
#                            accounts=accounts)


@app.route('/constructor', methods=['GET', 'POST'])
def constructor():
    name_error = ""
    if request.method == "POST":
        if "make" in request.form:
            weight = request.form["weight"]
            height = request.form["height"]
            name = request.form["name"]
            if not name:
                name_error = "Название не должно быть пустым"
            elif name in list(map(lambda x: x[2], User_().get_beds())):
                name_error = "Грядка с таким именем уже существует"
            elif '/' in name or '\\' in name or '.' in name:
                name_error = "Недопустимые символы"
            else:
                return redirect(f"/make_bed/{weight}/{height}/{name}")
        else:
            id_to_del = -1
            for k, v in request.form.items():
                if k.startswith("delete"):
                    id_to_del = int(k.split('_')[1])
                    User_().delete_bed(id_to_del)
                    break

            else:
                id = get_id_from_request_form(request.form).pop()
                return redirect(f"/make_bed/{-1}/{-1}/{-1}/{id}")

    beds = User_().get_beds()
    return render_template("constructor.html", active_cg="text-white", main="Журнал", name_error=name_error,
                           user=session.get('email'), beds=beds, test=123, chart_data=123)


@app.route('/make_bed/<width>/<height>/<name>', methods=['GET', 'POST'])
@app.route('/make_bed/<width>/<height>/<name>/<id>', methods=['GET', 'POST'])
def make_bed(width, height, name, id=None):
    data = ''
    if id:
        data = json.loads(User_().get_beds(id)[0][3])
        width = data['width']
        height = data['height']
        name = data['name']

    if request.method == "POST":
        if "save" in request.form:
            return redirect(url_for('constructor'))

    plants = Plants_().get_plants_idname(include_users=True, img=True)
    return render_template("make_bed.html", active_cg="text-white", width=width, height=height, name=name,
                           id=id, data=data,
                           plants=plants, user=session.get('email'))


@app.route('/add_plants', methods=['GET', 'POST'])
def add_plants():
    user_plants = Plants_().get_user_plants_id()
    plants = Plants_().get_plants_idname()
    plant_input_placeholder = ""
    if request.method == "POST":
        if "search" in request.form:
            search = request.form["plant_input"]
            plant_input_placeholder = search
            plants = Plants_().get_plants_idname(search)
        elif "save" in request.form:
            ids = []
            for k, v in request.form.items():
                if v == "on":
                    ids.append(int(k))
            Plants_().save_plants_to_user(ids)
            return redirect("/user_plants")
        elif "create_plant" in request.form:
            return redirect("/create_plant")

    return render_template("add_plants.html", active_up="text-white", main="Журнал", user=session.get('email'),
                           user_plants=user_plants, plants=plants, plant_input_placeholder=plant_input_placeholder)


@app.route('/plant/<plant_id>', methods=['GET', 'POST'])
def plant(plant_id):
    info = list(Plants_().get_plants_idname(id=plant_id)[0])
    description = json.loads(
        User_().get_user_plants_adds().get(info[0], info[2]).replace("\'", "\"").replace("extra_infromation",
                                                                                         "Доп. информация"))

    name = info[1]

    if os.path.isdir('static/' + session.get('email')) and name + '.jpg' in os.listdir(
            'static/' + session.get('email')):
        filename = session.get('email') + '/' + name + '.jpg'
    elif name in Plants_().get_all_plants_names(include_users=False) or name + '.jpg' in os.listdir('static/'):
        filename = name + '.jpg'
    else:
        filename = "image_placeholder.jpg"

    if request.method == "POST":
        if 'edit' in request.form:
            return redirect(f"/edit_plant/{plant_id}")
        elif "delete" in request.form:
            User_().delete_plant_from_user(plant_id, name, filename)
            return redirect("/user_plants")
        elif "reset" in request.form:
            User_().delete_plant_from_user(plant_id, name, m_type=True)
            return redirect(f"/plant/{plant_id}")
        elif 'history' in request.form:
            return redirect(f"/history/{plant_id}")

    return render_template("plant.html", user=session.get("email", 0), filename=filename, description=description,
                           name=name)


@app.route('/edit_plant/<plant_id>', methods=['GET', 'POST'])
def edit_plant(plant_id):
    info = list(Plants_().get_plants_idname(id=plant_id)[0])
    description = json.loads(
        User_().get_user_plants_adds().get(info[0], info[2]).replace("\'", "\"").replace("extra_infromation",
                                                                                         "Доп. информация"))
    for i in plant_params:
        if i not in description.keys():
            description[i] = ''
    name = info[1]

    if not os.path.isdir('static/' + session.get('email')):
        os.mkdir('static/' + session.get('email'))

    if os.path.isdir('static/' + session.get('email')) and name + '.jpg' in os.listdir(
            'static/' + session.get('email')):
        filename = session.get('email') + '/' + name + '.jpg'
    elif name in Plants_().get_all_plants_names(include_users=False) or name + '.jpg' in os.listdir('static/'):
        filename = name + '.jpg'
    else:
        filename = "image_placeholder.jpg"

    if request.method == "POST":
        if "save" in request.form:
            file = request.files['image']
            d = dict()
            for k, v in request.form.items():
                if k == 'image' or k == 'save':
                    continue
                if v:
                    d[k] = v
            User_().save_custom_adds(plant_id, d)
            if file.filename != '':
                file.save(os.path.join(f"static/{session.get('email')}", name + '.jpg'))
            return redirect(f"/plant/{plant_id}")

    return render_template("edit_plant.html", user=session.get("email", 0), filename=filename, description=description,
                           name=name)


@app.route('/history/<plant_id>', methods=['GET', 'POST'])
def history(plant_id):
    selected = 0
    m_type = "all"
    info = list(Plants_().get_plants_idname(id=plant_id)[0])
    name = info[1]
    if os.path.isdir('static/' + session.get('email')) and name + '.jpg' in os.listdir(
            'static/' + session.get('email')):
        filename = session.get('email') + '/' + name + '.jpg'
    elif name in Plants_().get_all_plants_names(include_users=False) or name + '.jpg' in os.listdir('static/'):
        filename = name + '.jpg'
    else:
        filename = "image_placeholder.jpg"

    if not session.get("date_changed", 0):
        cur_date = datetime.datetime.now().date()
        start_date = cur_date - datetime.timedelta(days=3)
        end_date = cur_date + datetime.timedelta(days=3)
        session["timefrom"] = start_date
        session["timeto"] = end_date
        session["date_changed"] = 1

    if request.method == "POST":
        if "date_picker" in request.form:
            start_date = datetime.datetime.strptime(request.form["timefrom"], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(request.form["timeto"], "%Y-%m-%d")
            session["date_changed"] = 1
            session["timefrom"] = start_date
            session["timeto"] = end_date

        elif "date_reset" in request.form:
            cur_date = datetime.datetime.now().date()
            start_date = cur_date - datetime.timedelta(days=3)
            end_date = cur_date + datetime.timedelta(days=3)
            session["timefrom"] = start_date
            session["timeto"] = end_date
        elif "m_type_btn" in request.form:
            m_type = request.form["m_type"]
            d = {"all": 0,
                 "watering": 1,
                 "planting": 2,
                 "tending": 3,
                 "harvesting": 4}
            selected = d[m_type]

    history = Plants_().get_plant_history(plant_id, m_type=m_type)
    new_his = []
    for i in history:
        timefrom = parse_date_string(session["timefrom"])
        timeto = parse_date_string(session["timeto"])
        if type(timefrom) == datetime.datetime:
            timefrom = timefrom.date()
        if type(timeto) == datetime.datetime:
            timeto = timeto.date()
        if i[-2] >= timefrom and i[-2] <= timeto:
            new_his.append(i)
    new_his.sort(key=lambda x: x[4])

    return render_template("history.html", user=session.get("email", 0), history=new_his, name=name, filename=filename,
                           time_from=parse_date_string(session.get("timefrom")),
                           time_to=parse_date_string(session.get("timeto")),
                           selected=selected)


@app.route('/create_plant', methods=['GET', 'POST'])
def create_plant():
    name_error = ''
    if request.method == "POST":
        if 'save' in request.form:
            name = request.form["name"]
            file = request.files['image']
            d = dict()
            extra_eng = ['location', 'reproduction', 'group', 'winterness', 'application', 'cultivation', 'soil',
                         'extra_information']
            extra_rus = ['Местоположение', 'Размножение', 'Группа', 'Зимостойкость', 'Применение', 'Выращивание',
                         'Требования к почве', 'Доп. информация']

            for i in range(len(extra_eng)):
                if request.form[extra_eng[i]] != '':
                    d[extra_rus[i]] = request.form[extra_eng[i]]
            if name.strip() == '':
                name_error = 'Неправильный формат имени'
            elif name in Plants_().get_all_plants_names(False) or name in [x[1] for x in Plants_().get_plants_idname(
                    include_users=True)]:
                name_error = 'Растение с данным именем уже существует'
            if file.filename == '':
                file = Image.open('static/image_placeholder.jpg')
            if name_error == '':
                if not os.path.exists(f"static/{session.get('email')}"):
                    os.makedirs(f"static/{session.get('email')}")
                file.save(os.path.join(f"static/{session.get('email')}", name + '.jpg'))
                Plants_().save_custom_plant(name, d)
                return redirect("user_plants")

    return render_template("create_plant.html", user=session.get("email", 0), name_error=name_error)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    accs = User_().get_user_tg()
    if request.method == "POST":
        for i in request.form:
            if i.startswith("delete"):
                User_().delete_tg(user_id=i.split('_')[1])

    return render_template("profile.html", user=session.get("email", 0), active_profile='text-white', accs=accs)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect("/login/")


def get_emails():  # Возвращает список emailов
    cur = mysql.connection.cursor()
    cur.execute("SELECT email FROM auth_data")
    res = cur.fetchall()
    cur.close()
    return [email[0] for email in res]


def get_date_by_id(button_id, day_list):  # Возвращает дату по id кнопки
    for i in day_list:
        if int(button_id) == i[0]:
            return i[1]


def parse_date_string(date_string):
    try:
        parsed_date = parse(date_string)
        return parsed_date
    except TypeError:
        return date_string


def get_id_from_request_form(r_form):
    plants_id = set()
    for i in r_form:
        if i.isnumeric():
            plants_id.add(int(i))
        elif i.split('_')[0].isnumeric():
            plants_id.add(int(i.split('_')[0]))
    return plants_id


def add_checked_for_plants(plants, ids):
    temp_plants = []
    for i in plants:
        i = list(i)
        if i[0] in ids:
            temp_plants.append(i + ["checked"])
        else:
            temp_plants.append(i + [""])
    return temp_plants


def get_lst_of_type(typeof, d):
    temp = defaultdict(int)
    for k, v in d:
        id = k[:k.find('_')]
        if k.endswith("_type") and v == typeof:
            temp[id] = 1
        elif k.endswith("_count") and id in temp.keys():
            temp[id] = v

    return list(map(lambda x: list(x), temp.items()))


def continue_act(plants):
    # user_plants = Plants_().get_user_plants_id()
    plants_id = get_id_from_request_form(request.form)
    # plants_to_save = plants_id - set(user_plants)
    # Plants_().save_plants_to_user(plants_to_save)
    plants = add_checked_for_plants(plants, get_id_from_request_form(request.form))
    plants_to_plant = Plants_().get_plants_idname(id=plants_id, img=True)
    return plants, plants_to_plant


def add_padding(lst, k):
    new_lst = []
    for i in lst:
        if type(i) == int:
            new_lst.append([i] + [0] * k)
        else:
            new_lst.append(i + [0] * k)
    return new_lst


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_reminder(d):
    info = d
    plants = []
    accounts = []
    for k, v in info.items():
        if k.isdigit():
            plants.append(k)
        elif k == "accounts":
            accounts.append(v)

    period = info["period"] + "_" + info["period_type"]

    with open('static/tg_data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        if len(file_data["data"]) == 0:
            id = 1
        else:
            id = file_data["data"][-1]["id"]
        addition = {"id": id + 1, "email": session.get("email"), "name": info["name"], "m_type": en_to_ru[info["m_type"]],
                    "tg_id": accounts, "plants": [x[1] for x in Plants_().get_plants_idname(id=plants)], "start_date": info["start_date"], "period": period,
                    "comment": info["comment"], "plants_ids": plants}
        file_data["data"].append(addition)
        file.seek(0)
        json.dump(file_data, file, indent=4)
    return


def save_plants(r):
    user_plants = Plants_().get_user_plants_id()
    plants_id = get_id_from_request_form(r)
    plants_to_save = plants_id - set(user_plants)
    Plants_().save_plants_to_user(plants_to_save)
    return


def sort_by_m_type(history, m_type):
    history = history
    d_r1 = {
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
    d_r2 = {1: "watering",
            2: "planting",
            3: "tending",
            4: "harvesting"}
    ids = [x[1] for x in history]
    plants_name = Plants_().get_plants_idname(id=ids)
    d = dict([[x[0], x[1]] for x in plants_name])
    new_his = []
    for i in range(len(history)):
        if d_r2[m_type] in history[i][2]:
            new_his.append(list(history[i]) + [d[history[i][1]]])

            new_his[-1][2] = d_r1[history[i][2]]
    return new_his


def transform_period(data):
    data = data
    for i in range(len(data)):
        n, s = data[i]["period"].split("_")
        res = ""
        n = int(n)
        if s == "day":
            if n == 0:
                res = "отсутствует"
            elif n == 1:
                res = "каждый день"
            elif n in [2, 3, 4]:
                res = f"каждые {n} дня"
            else:
                res = f"каждые {n} дней"
        elif s == "week":
            if n == 0:
                res = "отсутствует"
            elif n == 1:
                res = "каждую неделю"
            elif n in [2, 3, 4]:
                res = f"каждые {n} недели"
            else:
                res = f"каждые {n} недель"
        elif s == "month":
            if n == 0:
                res = "отсутствует"
            elif n == 1:
                res = "каждый месяц"
            elif n in [2, 3, 4]:
                res = f"каждые {n} месяца"
            else:
                res = f"каждые {n} месяцев"
        elif s == "hout":
            if n == 0:
                res = "отсутствует"
            elif n == 1:
                res = "каждый час"
            elif n in [2, 3, 4]:
                res = f"каждые {n} часа"
            else:
                res = f"каждые {n} часов"
        data[i]["period"] = res
    return data


@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template("error.html", text="Упс, похоже Вы пытаетесь загрузить слишком большой файл. Допустимый "
                                              "объём скачивания - 8мб.")


# API SECTION
@app.route('/todo/api/v1.0/emails', methods=['GET'])
def get_emails_api():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email, password FROM auth_data")
    res = cursor.fetchall()
    cursor.close()
    return jsonify({'data': [dict(res)]})


@app.route('/todo/api/v1.0/tg_emails', methods=['GET'])
def get_tg_emails():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM telegram_data")
    res = cursor.fetchall()
    cursor.close()
    return jsonify({'emails': res})


@app.route('/todo/api/v1.0/tg_registration', methods=['POST'])
def post_tg_account():
    data = request.json['tg_data']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO telegram_data (email, telegram_id, name) VALUES(%s, %s, %s)",
                   (data[0], data[1], data[2]))
    mysql.connection.commit()
    cursor.close()
    return "success", 200


def get_reminders():
    with open("static/tg_data.json", 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        data = file_data["data"]

        new_data = []

        for item in data:
            if item["email"] == session.get("email"):
                new_data.append(item)
        return new_data


def delete_reminder(id):
    with open("static/tg_data.json", 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        data = file_data["data"]

        new_data = []

        for item in data:
            if item["id"] != int(id):
                new_data.append(item)

        file_data["data"] = new_data
        file.seek(0)
        file.truncate()
        json.dump(file_data, file, indent=2)
        return


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
