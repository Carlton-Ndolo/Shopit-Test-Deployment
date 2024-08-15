#seller.py
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Product, Category, Order,OrderItem, Review, UserPayment
from flask_restful import Api, Resource
from config import cloudinary

seller_bp = Blueprint('seller_bp', __name__, url_prefix='/shopit/seller')
seller_api = Api(seller_bp)


class SellerProfile(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Get products for the seller
        products = Product.query.filter_by(seller_id=user_id).all()
        products_list = [
            {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else "Unknown",
                "image_url": product.image_url,
                "stock": product.stock
            }
            for product in products
        ]

        # Get orders for the seller
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(Product.seller_id == user_id).all()
        orders_list = []
        for order in orders:
            order_items = [
                {
                    "product_id": item.product_id,
                    "product_title": item.product.title,
                    "quantity": item.quantity,
                    "price": item.price
                } for item in order.order_items if item.product.seller_id == user_id
            ]

            if order_items:
                orders_list.append({
                    "order_id": order.id,
                    "buyer_id": order.buyer_id,
                    "total_price": order.total_price,
                    "status": order.status,
                    "created_at": order.created_at.isoformat(), 
                    "updated_at": order.updated_at.isoformat(),  
                    "order_items": order_items
                })

        profile = {
            "username": user.username,
            "email": user.email,
            "products": products_list,
            "orders": orders_list
        }

        return jsonify(profile)
    
    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        seller = User.query.get(user_id)

        if not seller or seller.role.id != 2:
            return {"error": "Unauthorized"}, 403

        data = request.json

        if 'username' in data:
            seller.username = data['username']
        if 'email' in data:
            seller.email = data['email']
        if 'password' in data:
            seller.password = data['password']

        seller.updated_at = datetime.now()
        db.session.commit()

        return {"message": "Profile updated successfully"}, 200

    # @jwt_required()
    # def delete(self):
    #     user_id = get_jwt_identity()
    #     seller = User.query.get(user_id)

    #     if not seller or seller.role.id != 2:
    #         return {"error": "Unauthorized"}, 403

    #     db.session.delete(seller)
    #     db.session.commit()

    #     return {"message": "Seller profile deleted"}, 200

class CreateProduct(Resource):
    @jwt_required()
    def post(self):
        data = request.form
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role.id != 2:
            return {"error": "Only sellers can create products"}, 403

        category = Category.query.filter_by(id=data['category_id']).first()

        if not category:
            return {"error": "Category not found"}, 404

        # Handle file upload
        image_url = ''
        if 'file' in request.files:
            file = request.files['file']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                image_url = upload_result.get('secure_url')

        product = Product(
            title=data['title'],
            description=data['description'],
            price=float(data['price']),
            category=category,
            image_url=image_url,
            seller_id=user_id,
            stock=int(data.get('stock', 0))
        )

        db.session.add(product)
        db.session.commit()

        return {"message": "Product created", "product": product.id}, 201

class GetProductsBySeller(Resource):
    @jwt_required()
    def get(self):
        
        user_id = get_jwt_identity()

        seller_id = user_id  

        products = Product.query.filter_by(seller_id=seller_id).all()

        if not products:
            return {"message": "No products found for this seller"}, 404
        return [
            {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else "Unknown",
                "image_url": product.image_url,
                "seller_id": product.seller_id,
                "stock": product.stock
            }
            for product in products
        ], 200

class UpdateProduct(Resource):
    @jwt_required()
    def put(self, product_id):
        data = request.form
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        product = Product.query.get_or_404(product_id)

        if not user or user.role.id != 2 or product.seller_id != user_id:
            return {"error": "Only the seller who created the product can update it"}, 403

        category = Category.query.filter_by(id=data['category_id']).first()
        if not category:
            return {"error": "Category not found"}, 404

        product.title = data['title']
        product.description = data['description']
        product.price = float(data['price'])
        product.category = category

        if 'file' in request.files:
            file = request.files['file']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                product.image_url = upload_result.get('secure_url')

        product.stock = int(data.get('stock', product.stock))
        product.updated_at = datetime.now()

        db.session.commit()
        return {"message": "Product updated", "product": product.id}, 200

class DeleteProduct(Resource):
    @jwt_required()
    def delete(self, product_id):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        product = Product.query.get_or_404(product_id)

        if not user or user.role.id != 2 or product.seller_id != user_id:
            return {"error": "Only the seller who created the product can delete it"}, 403

        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted"}, 200
    
class SellerOrders(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        seller = User.query.get(user_id)

        if not seller or seller.role.id != 2:
            return {"error": "Unauthorized"}, 403
        
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(Product.seller_id == user_id).all()

        orders_list = []
        for order in orders:
            buyer = User.query.get(order.buyer_id) 

            order_items = [
                {
                    "product_id": item.product_id,
                    "product_title": item.product.title,
                    "quantity": item.quantity,
                    "price": item.price,
                    "image_url":item.product.image_url
                } for item in order.order_items if item.product.seller_id == user_id
            ]

            if order_items:  
                orders_list.append({
                    "order_id": order.id,
                    "buyer_name": buyer.username, 
                    "description": f"Order by {buyer.first_name} {buyer.last_name}", 
                    "total_price": order.total_price,
                    "status": order.status,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "Order Items":order_items
                })

        return jsonify({"orders": orders_list})




class SellerOrderDetail(Resource):
    @jwt_required()
    def get(self, order_id):
        user_id = get_jwt_identity()
        seller = User.query.get(user_id)

        if not seller or seller.role.id != 2:
            return {"error": "Unauthorized"}, 403

        order = Order.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        buyer = User.query.get(order.buyer_id)  

        order_items = [
            {
                "product_id": item.product_id,
                "product_title": item.product.title,
                "quantity": item.quantity,
                "price": item.price
            } for item in order.order_items if item.product.seller_id == user_id
        ]

        order_detail = {
            "order_id": order.id,
            "buyer_username": buyer.username, 
            "buyer_full_name": f"{buyer.first_name} {buyer.last_name}", 
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "order_items": order_items
        }

        return jsonify({"order": order_detail})

class TotalSales(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        
        # Ensure the user is a seller
        if user.role.name != 'Seller':
            return {"error": "Unauthorized access"}, 403
        
        # Query for total sales from all orders
        total_sales = db.session.query(
            db.func.sum(OrderItem.price * OrderItem.quantity)
        ).join(Product).filter(Product.seller_id == user_id).scalar() or 0.0
        
        return {"total_sales": total_sales}, 200


class ProductSales(Resource):
    @jwt_required()
    def get(self, product_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        
        # Ensure the user is a seller
        if user.role.name != 'Seller':
            return {"error": "Unauthorized access"}, 403

        # Check if the product belongs to the seller
        product = Product.query.filter_by(id=product_id, seller_id=user_id).first()
        if not product:
            return {"error": "Product not found or does not belong to you"}, 404

        # Query for total sales of the specific product
        total_sales = db.session.query(
            db.func.sum(OrderItem.price * OrderItem.quantity)
        ).filter(OrderItem.product_id == product_id).scalar() or 0.0
        
        return {"product_id": product_id, "total_sales": total_sales}, 200
    
class SellerShopRating(Resource):
    @jwt_required()
    def get(self, seller_id):
        user_id = get_jwt_identity()

        if user_id != seller_id:
            return {"error": "Unauthorized access to ratings for this seller"}, 403

        products = Product.query.filter_by(seller_id=seller_id).all()

        if not products:
            return {"message": "No products found for this seller"}, 404

        total_rating = 0
        count = 0

        for product in products:
            reviews = Review.query.filter_by(product_id=product.id).all()
            for review in reviews:
                total_rating += review.rating
                count += 1

        if count == 0:
            return {"seller_id": seller_id, "average_rating": "N/A"}, 200

        average_rating = total_rating / count
        shop_rating_in_percentage = average_rating * 20

        formatted_rating = f"{shop_rating_in_percentage:.2f}%"

        return {"seller_id": seller_id, "average_rating": formatted_rating}, 200
    
class SellerProductPayments(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        
        # Ensure the user is a seller
        user = User.query.get_or_404(user_id)
        if user.role.name != 'Seller':
            return {"error": "Unauthorized access"}, 403
        
        # Query for all orders containing products from this seller
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(Product.seller_id == user_id).all()
        
        # Collect payment information
        payments_summary = {}
        for order in orders:
            buyer = User.query.get(order.buyer_id)
            for item in order.order_items:
                if item.product.seller_id == user_id:
                    if item.product_id not in payments_summary:
                        payments_summary[item.product_id] = {
                            "product_title": item.product.title,
                            "total_amount": 0.0,
                            "total_quantity": 0,
                            "buyers": set()
                        }
                    payments_summary[item.product_id]["total_amount"] += item.price * item.quantity
                    payments_summary[item.product_id]["total_quantity"] += item.quantity
                    payments_summary[item.product_id]["buyers"].add(buyer.username)

        # Format response
        payments_list = [
            {
                "product_id": product_id,
                "product_title": details["product_title"],
                "total_amount": details["total_amount"],
                "total_quantity": details["total_quantity"],
                "buyers": list(details["buyers"])
            }
            for product_id, details in payments_summary.items()
        ]
        
        return make_response(jsonify({"payments_summary": payments_list}), 200)


    
seller_api.add_resource(SellerProfile, '/profile')
seller_api.add_resource(CreateProduct, '/create_product')
seller_api.add_resource(GetProductsBySeller, '/products_by_seller')
seller_api.add_resource(UpdateProduct, '/product/<int:product_id>')
seller_api.add_resource(DeleteProduct, '/product/<int:product_id>')
seller_api.add_resource(SellerOrders, '/orders')
seller_api.add_resource(SellerOrderDetail, '/orders/<int:order_id>')
seller_api.add_resource(TotalSales, '/total_sales')
seller_api.add_resource(ProductSales, '/product_sales/<int:product_id>')
seller_api.add_resource(SellerShopRating, '/shop_rating/<int:seller_id>')
seller_api.add_resource(SellerProductPayments, '/product_payments')