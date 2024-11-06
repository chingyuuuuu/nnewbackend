from flask import Blueprint, request, jsonify, send_from_directory
from sqlalchemy.exc import SQLAlchemyError
import os

product_routes = Blueprint('product_routes', __name__)


@product_routes.route('/uploadproducts', methods=['POST'],endpoint='uploadproducts')
def save_product():
    from ..models import Product
    from ..import db

    # 獲得當前文件的目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 絕對路徑-上一級目錄當中
    uploads_folder = os.path.join(current_dir, '..', 'uploads')
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

    image_url=None #預設為none
    if 'image' in request.files:
        image_file = request.files['image']

        #圖片儲存在絕對路徑，但是資料庫儲存的是相對路徑
        image_path = os.path.join("uploads", image_file.filename)
        absolute_image_path = os.path.join(uploads_folder, image_file.filename)
        image_file.save(absolute_image_path)  # 保存文件到指定路径
        image_url = f"http://127.0.0.1:5000/{image_path.replace(os.sep, '/')}"

    data = request.form  # 请求数据
    user_id = int(data.get('user_id'))

    new_product = Product(
        name=data['name'],
        type=data['type'],
        price=data['price'],
        cost=data['cost'],
        quantity=data['quantity'],
        user_id=user_id,
        image=image_url  # 如果没有image，image_path 是 None
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify({
            "message": "Product saved successfully!",
            "image_url": image_url,
        }), 200
    except Exception as e:
        db.session.rollback()  # 如果提交失败，回滚会话
        print(f"Error occurred: {e}")  # 印具體的錯誤信息
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@product_routes.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    uploads_folder="uploads"
    return send_from_directory(uploads_folder, filename)

@product_routes.route('/getProducts',methods=['GET'])
def get_products():
    from ..models import Product
    try:
            user_id =request.args.get('user_id')
            if not user_id:
                return jsonify({"message":"User ID missing"}),400


            #將查詢結果轉換為json
            products = Product.query.filter_by(user_id=user_id).all()
            products_list=[]
            #遍歷每個商品並加入倒product_list
            for product in products:
                if product.image:
                    image_url = f"http://127.0.0.1:5000/{product.image}" if '/uploads/' not in product.image else product.image
                else:
                    image_url = None
                products_list.append({
                                'product_id':product.product_id,
                                'name': product.name,
                                'type': product.type,
                                'price': product.price,
                                'cost': product.cost,
                                'quantity': product.quantity,
                                'image':  image_url,
                            })

            return jsonify(products_list), 200
    except Exception as e:
        print(f"Error occurred while fetching products: {e}")  # 打印具體的錯誤信息
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@product_routes.route('/getprodctsinClient/',methods=['GET'])
def proudcts_in_Client():
    from ..models import Product
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"message": "User ID missing"}), 400

        # 將查詢結果轉換為json
        products = Product.query.filter_by(user_id=user_id).all()
        products_list = []
        # 遍歷每個商品並加入倒product_list
        for product in products:
            if product.image:
               image_url = f"http://127.0.0.1:5000/{product.image}" if '/uploads/' not in product.image else product.image
            else:
                image_url=None
            products_list.append({
                'product_id': product.product_id,
                'name': product.name,
                'type': product.type,
                'price': product.price,
                'image': image_url,
            })

        return jsonify(products_list), 200
    except Exception as e:
        print(f"Error occurred while fetching products: {e}")  # 打印具體的錯誤信息
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@product_routes.route('/getproducts/<int:productId>',methods=['GET'])
def get_one_product(productId):
    from ..models import Product
    try:
        #根據productId去資料庫找商品
        product = Product.query.get(productId)
        if product is None:
            return jsonify({"message":"Product not found"}),
        return jsonify({
             'product_id': product.product_id,
              'name':product.name,
             'type': product.type,
              'price': product.price,
              'cost': product.cost,
              'quantity': product.quantity,
        }),200
    except SQLAlchemyError as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500



@product_routes.route('/update_product/<int:productId>',methods=['PUT'])
def update_product(productId):#接收ProudctId
    from ..models import Product
    from .. import db
    data = request.get_json()#從前端獲取數據

    if not data:
        return jsonify({"message":"No data provided"}),400
    try:
        #用product_id查找產品
        product = Product.query.get(productId)
        if not product:
            #不存在,404
            return jsonify({"message":"Product not found"}),404

        #初始化變數-如果前端提供某個欄位的值就使用，如果沒有就用現有的資訊去初始化
        name = data.get('name') if 'name' in data else product.name
        type = data.get('type') if 'type' in data else product.type
        price = data.get('price') if 'price' in data else product.price
        cost = data.get('cost') if 'cost' in data else product.cost
        quantity = data.get('quantity') if 'quantity' in data else product.quantity

        is_modified =False

        # 確保只有在值發生變化時才會更新
        if name != product.name:
            product.name = name
            is_modified = True
        if type != product.type:
            product.type = type
            is_modified = True
        if price != product.price:
            product.price = price
            is_modified = True
        if cost != product.cost:
            product.cost = cost
            is_modified = True
        if quantity != product.quantity:
            product.quantity = quantity
            is_modified = True

        if not is_modified:
            return jsonify({"message": "No changes were made to the product."}), 200

        db.session.commit()

        return jsonify({
                "message": "Product updated successfully",
                'product_id': product.product_id,  # 返回产品ID
                'name': product.name,
                'type': product.type,
                'price': product.price,
                'cost': product.cost,
                'quantity': product.quantity
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message":"An error occurred","error":str(e)}),500

@product_routes.route('/delete_product/<int:productId>',methods=['DELETE'])
def delete_prodcut(productId):
    from ..models import Product
    from ..import db
    try:
        product =Product.query.get(productId)
        if not product:
            return jsonify({"message":"Product not found "}),404
        db.session.delete(product)
        db.session.commit()

        return jsonify({"message":"Product deleted successful!"}),200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message":"An error occurred","error":str(e)}),500


