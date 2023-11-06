from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, validators
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):  # Форма для логина
    email = StringField("Почта: ", validators=[Email()])
    password = PasswordField("Пароль: ", [DataRequired(),
                                          Length(min=4, max=20)])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):  # Форма для регистрации
    email = StringField("Почта: ", validators=[Email()])
    password = PasswordField("Пароль: ", [DataRequired(),
                                          Length(min=4, max=20),
                                          EqualTo('password_confirmation',
                                                  message='Пароли должны совпадать')])
    password_confirmation = PasswordField("Повторите пароль: ", [DataRequired(),
                                                                 Length(min=4, max=20)])
    submit = SubmitField("Зарегистрироваться")


class ForgotPassForm(FlaskForm):  # Форма для Сброса пароля
    email = StringField("Ваша почта: ", validators=[Email()])
    submit = SubmitField("Отправить")


class ResetPassForm(FlaskForm):  # Форма для обновления
    password = PasswordField("Новый пароль: ", [DataRequired(),
                                                Length(min=4, max=20),
                                                EqualTo('password_confirmation',
                                                        message='Пароли должны совпадать')])
    password_confirmation = PasswordField("Повторите пароль: ", [DataRequired(),
                                                                 Length(min=4, max=20)])
    submit = SubmitField("Сменить")
