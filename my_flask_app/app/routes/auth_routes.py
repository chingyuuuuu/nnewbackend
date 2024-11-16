import string
import random
from flask import Blueprint, request, jsonify,session
from sqlalchemy.exc import SQLAlchemyError
from my_flask_app.app.models import User
from flask_mail import Message
from werkzeug.security import generate_password_hash

auth_routes = Blueprint('auth_routes', __name__)


@auth_routes.route('/login', methods=['POST'])
def login():
    from ..models import User  # 延遲導入
    from werkzeug.security import check_password_hash

    data = request.get_json()  # 客戶端發送數據，用來解析json格式的數據
    account = data.get('account')
    password = data.get('password')

    if not account or not password:
        return jsonify({"message": "Account and password are required"}), 400

    try:  # 在database當中查找account and password
        user = User.query.filter_by(account=account).first()
        if not user:
            return jsonify({"message" : "Invalid username or password"}),401
        if check_password_hash(user.password,password):
            session['user_id']=user.user_id

            # 從後端傳送user_id到前端
            return jsonify({"message":"Login successful","user_id":str(user.user_id)})
        else:
            return jsonify({"message":"Invalid username or password"}),401

    except SQLAlchemyError as e:
        print(f"Error during login: {e}")
        return jsonify({"message": "An error occurred", "error": str(e)}), 500





@auth_routes.route('/register', methods=['POST'])
def register():
    from .. import db
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    account = data.get('account')
    password = data.get('password')

    if not account or not password:
        return jsonify({"message": "Account and password are required"}), 400

    try:
        existing_user = User.query.filter_by(account=account).first()  #獲取第一條訊息
        if existing_user:
            return jsonify({"message": "account already exists"}), 409

        # 創建新用戶
        hashed_password = generate_password_hash(password)
        new_user = User(account=account, password= hashed_password)
        db.session.add(new_user)#加入database
        db.session.commit()#儲存到database

        return jsonify({"message": "User registered successfully", "user_id": new_user.user_id}),200

    except SQLAlchemyError as e:#用於捕獲數據庫異常
        db.session.rollback()  # 撤销所有更改
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@auth_routes.route('/forget_password',methods=['POST'])
def forget_password():
    from .. import mail
    from .. import db
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"message":"Email is required"}),400

    email = data.get('email')#從客戶端的數據中，取得email對應值
    if not email:
        return jsonify({"message": "Email is required"}), 400
    user = User.query.filter_by(account=email).first()#找到account
    if not user:
        return jsonify({"message":"User not found"}),404


    #生成驗證碼
    token = ''.join(random.choices(string.ascii_letters + string.digits,k=6))#join元素串接
    user.reset_token = token #更新用戶的token
    db.session.commit()

    #發送郵件
    #Message-是flask-mail提供的一個類，用於創建email消息對象
    try:
        msg = Message('Password Reset Code', sender='plankcanon78@gmail.com', recipients=[email])
        msg.body = f'Your password reset code is: {token}'
        mail.send(msg)
        return jsonify({"message": "Reset code sent"}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"message": "Failed to send email"}), 500

@auth_routes.route('/verify',methods=['POST'])
def verify():
    from ..import db
    try:
            data = request.get_json()
            #檢查是否提供驗證碼
            if  'code' not in data:
                return jsonify({'message':'缺少驗證碼'}),400

            email = data['email']
            code = data['code']
            user=User.query.filter_by(account=email).first()
            if not user:
                return jsonify({'message': '該用戶不存在'}), 404

            #驗證碼是否匹配
            if user.reset_token == code:
                #驗證通過
               user.reset_token= None #清除token
               db.session.commit()
               return jsonify({'message':'驗證成功!'}),200
            else:
                return jsonify({'message':'驗證碼錯誤'}),400

    except Exception as e:
        return jsonify({'message': '服務器錯誤', 'error': str(e)}), 500

@auth_routes.route('/update_password', methods=['POST'])
def update_password():
    from ..import db
    from werkzeug.security import generate_password_hash

    try:
        data = request.get_json()

        # 检查是否提供了所有必需的字段
        if not all(key in data for key in ('email', 'new_password', 'confirm_password')):
            return jsonify({'message': 'Missing required fields'}), 400

        email = data.get('email')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')


        if new_password != confirm_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        # 找到用户
        user = User.query.filter_by(account=email).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        #檢查密碼長度
        if len(new_password) < 8:
            return jsonify({'message': 'New password must be at least 8 characters'}), 400

        # 更新用戶密碼
        user.password = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({'message': 'Password updated successfully!'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'message': 'Server error', 'error': str(e)}), 500
