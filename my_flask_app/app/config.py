import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    #database
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY')

    # 其他
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    TESTING = os.getenv('TESTING', 'False') == 'True'

    #Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'

    #API
    HF_API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-2.7B"  # 可更改為其他模型
    HF_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")#從env中讀取api token
