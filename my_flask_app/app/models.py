from sqlalchemy import Column, Integer, String, DateTime
from .extensions import db
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class User(db.Model):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    account = Column(String(80), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    reset_token = Column(String(80), nullable=True)
    reset_token_created_at = Column(DateTime, nullable=True)  # 添加生成时间字段

    def __init__(self, account, password, reset_token=None):
        self.account = account
        self.password = password
        self.reset_token = reset_token
        self.reset_token_created_at = None  # 預設，時間是none

    def set_reset_token(self, token):
        self.reset_token = token
        self.reset_token_created_at = datetime.utcnow()  # 當前時間
        db.session.commit()

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_created_at = None  # 清除生成时间
        db.session.commit()

    def is_reset_token_valid(self, token, expiration_seconds=3600):
        if self.reset_token != token:
            return False

        # 确保 reset_token_created_at 存在且不为 None
        if self.reset_token_created_at is None:
            return False

        elapsed_time = (datetime.utcnow() - self.reset_token_created_at).total_seconds()
        return elapsed_time < expiration_seconds


class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(45), nullable=False)
    type = db.Column(db.String(45), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    image = db.Column(db.String(200))

    order_products = relationship('OrderProduct', back_populates='product')


class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    table = db.Column(db.String(50), nullable=False)  # 桌号
    total_amount = db.Column(db.Integer, nullable=False)  # 总金额
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 创建时间
    check = db.Column(db.Boolean, default=False)  # 用于检查订单状态（可选）
    user_id = db.Column(db.Integer, nullable=False)
    remark=db.Column(db.String(255),nullable=True)#可以讓客人加入備註
    # 加入與OrderProduct的關係
    order_products = relationship('OrderProduct', back_populates='order')

    def __init__(self, table, total_amount, user_id,remark=None):  # 确保创建 Order 所有必要的属性都被正确地初始化
        self.table = table
        self.total_amount = total_amount
        self.user_id = user_id
        self.remark= remark

    def __repr__(self):
        return f'<Order {self.order_id}: Table {self.table}, Total {self.total_amount}>'


class OrderProduct(db.Model):
    __tablename__ = 'orderproduct'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    # 加入Order and Product的雙向關係
    order = relationship('Order', back_populates='order_products')
    product = relationship('Product', back_populates='order_products')

    def __init__(self, order_id, product_id, quantity):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity

    def __repr__(self):
        return f'<OrderProduct Order ID {self.order_id}, Product ID {self.product_id}, Quantity {self.quantity}>'


class QA(db.Model):
   __tablename__ = 'qa'
   QA_id=db.Column(db.Integer,primary_key=True)
   type=db.Column(db.String(45),nullable=True)
   question=db.Column(db.String(100),nullable=False)
   answer=db.Column(db.String(100),nullable=False)
   image=db.Column(db.String(100),nullable=True)
   quser_id=db.Column(db.Integer,nullable=False)
   def __init__(self,type,question,answer,image,quser_id):
       self.type=type
       self.question=question
       self.answer=answer
       self.image=image
       self.quser_id=quser_id

class UnansweredQuestions(db.Model):
     __tablename__="Unansweredquestions"
     id=db.Column(db.Integer,primary_key=True)
     question=db.Column(db.String(100),nullable=False)
     occurence_count=db.Column(db.Integer,default=1)
     created_at=db.Column(db.DateTime,default=datetime.now(timezone.utc))
     updated_at=db.Column(db.DateTime,default=datetime.now(timezone.utc))
     fk_user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)

     def __repr__(self):
         return f"<UnansweredQuestions(id={self.id}, question={self.question}, occurrence_count={self.occurrence_count})>"
