import os


class Config:
    SECRET_KEY = 'ключ'  # Обязательно!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False