from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta

order_routes = Blueprint('order_routes', __name__)


@order_routes.route('/saveorder', methods=['POST'])
def save_order():
    from ..models import Order, OrderProduct
    from ..import db

    data = request.get_json()

    if not all(key in data for key in ('table', 'products', 'total_amount')):
        return jsonify({"message": "Missing required fields"}), 400

    table_number = data['table']
    products = data['products']  # products 是一個包含 product_id 和 quantity 的列表
    total_amount = data['total_amount']
    user_id = int(data['user_id'])
    remark=data.get('remark')#獲取remark,default=none,不會拋出異常
    try:
        # 建立新的訂單
        new_order=Order(
            table=table_number,
            total_amount=total_amount,
            user_id=user_id,
            remark=remark,
        )
        db.session.add(new_order)
        db.session.commit()  # 先提交以生成新的order_id

        # 保存每個商品到OrderProduct
        for product in products:
            product_id=product['product_id']
            quantity=product['quantity']

            order_product=OrderProduct(
                order_id=new_order.order_id,
                product_id=product_id,
                quantity=quantity,
            )

            db.session.add(order_product)
        db.session.commit()
        return jsonify({"message":"Order saved successfully!","order_id":new_order.order_id}),200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error while saving order: {e}")
        return jsonify({"message": "An error occurred", "error": str(e)}), 500



@order_routes.route('/getorder/<int:user_id>',methods=['GET'])
def get_all_orders(user_id):
    from ..models import Order
    try:
            orders=Order.query.filter_by(user_id=user_id).all()

            order_data=[]
            for order in orders:
                order_data.append({
                    "order_id":order.order_id,
                    "table":order.table,
                    "total_amount":order.total_amount,
                    "created_at": order.created_at.strftime('%Y-%m-%dT%H:%M:%S'), # 格式化日期
                    "remark":order.remark,
                    "check":order.check,
                    "is_active":order.is_active,
                })
            return jsonify(order_data),200
    except Exception as e:
        print(f'Error{e}')
        return jsonify({"error":str(e)}),500





@order_routes.route('/getorderforclient/<string:tableNumber>',methods=['GET'])
def get_order_for_client(tableNumber):
    from ..models import Order
    try:
        #根據桌號從database中取得訂單的邏輯
        orders=Order.query.filter_by(table=tableNumber).all()
        if not orders:
            return jsonify({"message": "No orders found for this table"}), 404
        order_data=[]
        for order in orders:
                order_data.append({
                    "order_id":order.order_id,
                    "table_number":order.table,
                    "total_amount":order.total_amount,
                    "created_at":order.created_at.isoformat()#加入創建時間
                })

        return jsonify({"orders":order_data}),200
    except Exception as e:
        print(f"error${e}")
        return jsonify({"error":str(e)}),500

#點擊訂單之後，查看商品資訊
@order_routes.route('/getorderdetail/<int:orderId>',methods=['GET'])
def get_order_details(orderId):
     from ..models import OrderProduct,Product
     try:
         #根據order_id找到該訂單所有商品
         order_products=OrderProduct.query.filter_by(order_id=orderId).all()

         if not order_products:
             return  jsonify({"message":"No products found for this order "}),404

         product_data=[]
         for op in order_products:
             product=Product.query.get(op.product_id)#根據product_id找到商品
             if product:
                 product_data.append({
                     "product_name":product.name,
                     "price":product.price,
                     "quantity":op.quantity,
                 })
             else:
                 return jsonify({"message":"Product not found for product_id:{}".format(op.product_id)}), 404

         return jsonify({
                 "order_id":orderId,
                 "products":product_data
         }),200
     except Exception as e:
          return jsonify({"error":str(e)}),500

@order_routes.route('/refresh_orders',methods=['POST'])
def refresh_orders():
    from ..models import Order,db
    try:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        Order.query.filter(Order.created_at >= today_start, Order.created_at < today_end).update({"is_active": False})
        db.session.commit()
        return jsonify({"message":"已刷新今日訂單"}),200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":str(e)}),500




