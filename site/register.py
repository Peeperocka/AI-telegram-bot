from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-123'  # Замените на надежный ключ!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


# Форма регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


# Маршруты
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверка на существующего пользователя
        user_by_email = User.query.filter_by(email=form.email.data).first()
        user_by_username = User.query.filter_by(username=form.username.data).first()

        if user_by_email or user_by_username:
            flash('Такой email или логин уже зарегистрирован!', 'error')
            return redirect(url_for('register'))

        # Создание нового пользователя
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('login'))  # Предполагается, что есть страница входа

    return render_template('register.html', form=form)


# Создание таблиц и запуск
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаст файл ite.db с таблицами
    app.run(debug=True)