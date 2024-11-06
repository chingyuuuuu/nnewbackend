from flask import Blueprint, jsonify
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from flask_mail import Message

main_routes = Blueprint('main_routes', __name__)


@main_routes.route('/api/data')
def get_data():
    return jsonify({'message': 'Hello from Flask!'})


@main_routes.route('/')
def home():
    return 'Welcome to the home page!'


@main_routes.route('/test_db', methods=['GET'])
def test_db():
    from .. import db
    try:
        db.session.execute(text('SELECT 1'))
        return 'Database connection is successful!', 200
    except OperationalError:
        return 'Database connection failed!', 500


@main_routes.route('/send_email')
def send_email():
    from .. import mail
    msg = Message('Hello', sender='your_email@gmail.com', recipients=['recipient@example.com'])
    msg.body = 'This is a test email.'
    try:
        mail.send(msg)
        return 'Email sent!'
    except Exception as e:
        return f'Failed to send email: {e}'
