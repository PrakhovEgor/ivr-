import datetime
import pickle

from flask import Flask, render_template, request, redirect, session, flash
from forms.auth_form import LoginForm, RegisterForm, ForgotPassForm, ResetPassForm, action_form
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import random
import string
import locale
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bf&*gyusdgf^Sggf78y5sj'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'main_data'

mysql = MySQL(app)

with open('tools/res2.pkl', 'rb') as file:
    res = pickle.load(file)



@app.route('/', methods=["POST", "GET"])
def main():
    for i in res:
        name = i["name"].replace("?", "")
        i.pop("name")
        i.pop("img_src")
        des = i


        cursor = mysql.connection.cursor()
        cursor.execute(' INSERT INTO plants(plant_name, description) VALUES(%s,%s)', (name, json.dumps(des, ensure_ascii=False).encode('utf8')))
        mysql.connection.commit()
        cursor.close()
    return ")"


def upload_data(res):
    print("fdh")
    for i in res:
        cursor = mysql.connection.cursor()
        cursor.execute(' INSERT INTO plants(plant_name, description) VALUES(%s,%s)', (i[0], i[2]))
        mysql.connection.commit()
        cursor.close()

app.run(debug=True)